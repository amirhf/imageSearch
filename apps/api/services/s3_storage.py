"""
S3-compatible storage implementation.
Works with AWS S3, Cloudflare R2, MinIO, and other S3-compatible services.
"""
import os
import io
from typing import Optional
from PIL import Image, ImageOps
import asyncio
import boto3
from botocore.exceptions import ClientError

from apps.api.services.image_storage import ImageStorage, ImageMetadata


class S3Storage(ImageStorage):
    """S3-compatible storage with support for AWS S3, Cloudflare R2, MinIO"""
    
    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region_name: str = "auto",
        thumbnail_size: int = 256,
        public_url_base: Optional[str] = None,
        use_presigned_urls: bool = True,
        presigned_url_expiry: int = 3600
    ):
        """
        Initialize S3-compatible storage.
        
        Args:
            bucket_name: S3 bucket name
            endpoint_url: S3 endpoint (None for AWS, custom for MinIO/R2)
            access_key_id: AWS/S3 access key
            secret_access_key: AWS/S3 secret key
            region_name: AWS region or 'auto' for R2
            thumbnail_size: Thumbnail dimensions (square)
            public_url_base: Base URL for public access (if bucket is public)
            use_presigned_urls: Generate presigned URLs for downloads
            presigned_url_expiry: Presigned URL expiry in seconds
        """
        self.bucket_name = bucket_name
        self.thumbnail_size = thumbnail_size
        self.public_url_base = public_url_base
        self.use_presigned_urls = use_presigned_urls
        self.presigned_url_expiry = presigned_url_expiry
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name,
            config=boto3.session.Config(signature_version='s3v4')
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    print(f"✓ Created S3 bucket: {self.bucket_name}")
                except Exception as create_error:
                    print(f"Warning: Could not create bucket {self.bucket_name}: {create_error}")
            else:
                print(f"Warning: Error checking bucket {self.bucket_name}: {e}")
    
    def _get_object_key(self, image_id: str, is_thumbnail: bool = False) -> str:
        """Get S3 object key for image"""
        prefix = "thumbnails/" if is_thumbnail else "images/"
        shard = image_id[:2]
        return f"{prefix}{shard}/{image_id}"
    
    def _find_existing_key(self, image_id: str, is_thumbnail: bool = False) -> Optional[str]:
        """Find existing S3 object key with correct extension by probing common formats."""
        base_key = self._get_object_key(image_id, is_thumbnail)
        for fmt in ['jpeg', 'jpg', 'png', 'webp']:
            key = f"{base_key}.{fmt}"
            try:
                # head_object is cheap and does not download the body
                self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
                return key
            except ClientError as e:
                err = e.response.get('Error', {}).get('Code')
                if err in ('404', 'NoSuchKey', 'NotFound'):
                    continue
                else:
                    # Log and continue trying other formats
                    print(f"Error checking key {key}: {e}")
                    continue
        return None
    
    async def save_image(
        self, 
        image_id: str, 
        image_bytes: bytes,
        generate_thumbnail: bool = True
    ) -> ImageMetadata:
        """Save image to S3 and generate thumbnail"""
        # Detect format and dimensions (EXIF-correct orientation)
        img = Image.open(io.BytesIO(image_bytes))
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        format_str = img.format.lower() if img.format else 'jpeg'
        width, height = img.size
        # Re-encode EXIF-corrected image for storage
        orig_buffer = io.BytesIO()
        save_kwargs = {}
        if format_str in ('jpeg', 'jpg'):
            save_kwargs = {"quality": 95, "optimize": True}
        img.save(orig_buffer, format=format_str.upper(), **save_kwargs)
        orig_bytes = orig_buffer.getvalue()
        size_bytes = len(orig_bytes)
        
        # Determine content type
        content_type_map = {
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp'
        }
        content_type = content_type_map.get(format_str, 'image/jpeg')
        
        # Save original (EXIF-corrected) image to S3
        object_key = self._get_object_key(image_id) + f".{format_str}"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=orig_bytes,
                ContentType=content_type,
                Metadata={
                    'width': str(width),
                    'height': str(height),
                    'format': format_str
                }
            )
        )
        
        # Generate and save thumbnail
        thumbnail_key = None
        if generate_thumbnail:
            thumbnail_key = await self._generate_thumbnail(image_id, img, format_str)
        
        return ImageMetadata(
            image_id=image_id,
            file_path=object_key,
            format=format_str,
            size_bytes=size_bytes,
            width=width,
            height=height,
            thumbnail_path=thumbnail_key
        )
    
    async def _generate_thumbnail(
        self, 
        image_id: str, 
        img: Image.Image, 
        format_str: str
    ) -> str:
        """Generate and save thumbnail to S3"""
        # Create thumbnail (use EXIF-corrected image)
        thumb = img.copy()
        thumb.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        thumb_buffer = io.BytesIO()
        thumb.save(thumb_buffer, format=format_str.upper())
        thumb_bytes = thumb_buffer.getvalue()
        
        # Determine content type
        content_type_map = {
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp'
        }
        content_type = content_type_map.get(format_str, 'image/jpeg')
        
        # Save to S3
        thumbnail_key = self._get_object_key(image_id, is_thumbnail=True) + f".{format_str}"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=thumbnail_key,
                Body=thumb_bytes,
                ContentType=content_type
            )
        )
        
        return thumbnail_key
    
    async def get_image(self, image_id: str) -> Optional[bytes]:
        """Retrieve original image bytes from S3"""
        # Try common formats
        for fmt in ['jpeg', 'jpg', 'png', 'webp']:
            object_key = self._get_object_key(image_id) + f".{fmt}"
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=object_key
                    )
                )
                return response['Body'].read()
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchKey':
                    print(f"Error retrieving {object_key}: {e}")
        return None
    
    async def get_thumbnail(self, image_id: str) -> Optional[bytes]:
        """Retrieve thumbnail bytes from S3"""
        # Try common formats
        for fmt in ['jpeg', 'jpg', 'png', 'webp']:
            thumbnail_key = self._get_object_key(image_id, is_thumbnail=True) + f".{fmt}"
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=thumbnail_key
                    )
                )
                return response['Body'].read()
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchKey':
                    print(f"Error retrieving {thumbnail_key}: {e}")
        return None
    
    async def delete_image(self, image_id: str) -> bool:
        """Delete image and thumbnail from S3"""
        deleted = False
        loop = asyncio.get_event_loop()
        
        # Delete original
        for fmt in ['jpeg', 'jpg', 'png', 'webp']:
            object_key = self._get_object_key(image_id) + f".{fmt}"
            try:
                await loop.run_in_executor(
                    None,
                    lambda: self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=object_key
                    )
                )
                deleted = True
            except ClientError:
                pass
        
        # Delete thumbnail
        for fmt in ['jpeg', 'jpg', 'png', 'webp']:
            thumbnail_key = self._get_object_key(image_id, is_thumbnail=True) + f".{fmt}"
            try:
                await loop.run_in_executor(
                    None,
                    lambda: self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=thumbnail_key
                    )
                )
            except ClientError:
                pass
        
        return deleted
    
    def get_image_url(self, image_id: str) -> str:
        """Get URL for image download"""
        if self.public_url_base:
            # Use public URL if configured
            existing_key = self._find_existing_key(image_id)
            if existing_key:
                return f"{self.public_url_base}/{existing_key}"
            # Fall through to presigned/API if not found
        elif self.use_presigned_urls:
            # Generate presigned URL
            try:
                # Try common formats
                for fmt in ['jpeg', 'jpg', 'png', 'webp']:
                    object_key = self._get_object_key(image_id) + f".{fmt}"
                    try:
                        url = self.s3_client.generate_presigned_url(
                            'get_object',
                            Params={
                                'Bucket': self.bucket_name,
                                'Key': object_key
                            },
                            ExpiresIn=self.presigned_url_expiry
                        )
                        return url
                    except:
                        continue
            except Exception as e:
                print(f"Error generating presigned URL: {e}")
        
        # Fallback to API endpoint
        return f"http://localhost:8000/images/{image_id}/download"
    
    def get_thumbnail_url(self, image_id: str) -> str:
        """Get URL for thumbnail download"""
        if self.public_url_base:
            # Use public URL if configured
            existing_thumb_key = self._find_existing_key(image_id, is_thumbnail=True)
            if existing_thumb_key:
                return f"{self.public_url_base}/{existing_thumb_key}"
            # Fall through to presigned/API if not found
        elif self.use_presigned_urls:
            # Generate presigned URL
            try:
                # Try common formats
                for fmt in ['jpeg', 'jpg', 'png', 'webp']:
                    thumbnail_key = self._get_object_key(image_id, is_thumbnail=True) + f".{fmt}"
                    try:
                        url = self.s3_client.generate_presigned_url(
                            'get_object',
                            Params={
                                'Bucket': self.bucket_name,
                                'Key': thumbnail_key
                            },
                            ExpiresIn=self.presigned_url_expiry
                        )
                        return url
                    except:
                        continue
            except Exception as e:
                print(f"Error generating presigned URL: {e}")
        
        # Fallback to API endpoint
        return f"http://localhost:8000/images/{image_id}/thumbnail"

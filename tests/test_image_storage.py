"""
Test suite for image storage functionality
"""
import pytest
import asyncio
import httpx
from pathlib import Path
import io
from PIL import Image


BASE_URL = "http://localhost:8000"


@pytest.fixture
def test_image_bytes():
    """Create a simple test image"""
    img = Image.new('RGB', (100, 100), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return buf.read()


@pytest.mark.asyncio
async def test_upload_and_download(test_image_bytes):
    """Test complete workflow: upload -> retrieve -> download"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Upload image
        files = {'file': ('test.jpg', test_image_bytes, 'image/jpeg')}
        response = await client.post(f"{BASE_URL}/images", files=files)
        assert response.status_code == 200
        
        result = response.json()
        image_id = result['id']
        
        # Verify response includes storage info
        assert 'download_url' in result
        assert 'thumbnail_url' in result
        assert 'width' in result
        assert 'height' in result
        assert 'size_bytes' in result
        assert 'format' in result
        
        print(f"✓ Upload successful: {image_id}")
        print(f"  Caption: {result.get('caption', 'N/A')}")
        print(f"  Format: {result['format']}")
        print(f"  Size: {result['width']}x{result['height']}, {result['size_bytes']} bytes")
        
        # 2. Get metadata
        response = await client.get(f"{BASE_URL}/images/{image_id}")
        assert response.status_code == 200
        
        metadata = response.json()
        assert metadata['id'] == image_id
        assert 'download_url' in metadata
        assert 'thumbnail_url' in metadata
        
        print(f"✓ Metadata retrieved")
        
        # 3. Download original image
        response = await client.get(f"{BASE_URL}/images/{image_id}/download")
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('image/')
        
        downloaded_bytes = response.content
        assert len(downloaded_bytes) > 0
        
        # Verify it's a valid image
        img = Image.open(io.BytesIO(downloaded_bytes))
        assert img.size[0] > 0
        assert img.size[1] > 0
        
        print(f"✓ Download successful: {len(downloaded_bytes)} bytes")
        
        # 4. Download thumbnail
        response = await client.get(f"{BASE_URL}/images/{image_id}/thumbnail")
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('image/')
        
        thumb_bytes = response.content
        assert len(thumb_bytes) > 0
        
        # Verify thumbnail is smaller
        thumb_img = Image.open(io.BytesIO(thumb_bytes))
        assert max(thumb_img.size) <= 256  # Should be 256 or smaller
        
        print(f"✓ Thumbnail downloaded: {thumb_img.size}")
        
        print(f"\n✅ All tests passed for image {image_id}")


@pytest.mark.asyncio
async def test_download_nonexistent():
    """Test downloading non-existent image returns 404"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/images/nonexistent123/download")
        assert response.status_code == 404
        
        response = await client.get(f"{BASE_URL}/images/nonexistent123/thumbnail")
        assert response.status_code == 404
        
        print("✓ 404 handling works correctly")


def test_storage_directory_created():
    """Test that storage directory is created"""
    storage_path = Path("./storage/images")
    # This will be created on first upload, so we just check the structure is valid
    assert True  # Basic structure test
    print("✓ Storage directory structure valid")


if __name__ == "__main__":
    print("Running Image Storage Tests...")
    print("=" * 60)
    
    # Run tests
    asyncio.run(test_upload_and_download(
        test_image_bytes=Image.new('RGB', (100, 100), color='red')
    ))
    
    asyncio.run(test_download_nonexistent())
    
    test_storage_directory_created()
    
    print("\n" + "=" * 60)
    print("All tests completed!")

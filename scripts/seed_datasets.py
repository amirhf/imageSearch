"""
Enhanced dataset seeding script for COCO, Unsplash, and other image datasets.
Downloads images and ingests them into the ImageSearch system with proper attribution.

Usage:
    python scripts/seed_datasets.py --dataset coco --count 1000
    python scripts/seed_datasets.py --dataset unsplash --count 500 --api-key YOUR_KEY
    python scripts/seed_datasets.py --list
"""
import asyncio
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import httpx
from tqdm import tqdm
import zipfile
import io


class DatasetSeeder:
    """Base class for dataset seeders"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=60.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def ingest_image(self, image_url: str, metadata: Dict) -> Optional[Dict]:
        """Ingest a single image from URL"""
        try:
            # Send as form data with url field
            form_data = {"url": image_url}
            response = await self.session.post(
                f"{self.api_url}/images",
                data=form_data
            )
            response.raise_for_status()
            result = response.json()
            result["metadata"] = metadata
            return result
        except Exception as e:
            print(f"Error ingesting {image_url}: {e}")
            return None
    
    async def seed(self, count: int, **kwargs) -> List[Dict]:
        """Seed images from dataset"""
        raise NotImplementedError


class COCOSeeder(DatasetSeeder):
    """Seeds images from COCO 2017 validation dataset"""
    
    ANNOTATIONS_URL = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
    IMAGES_BASE_URL = "http://images.cocodataset.org/val2017"
    
    async def download_annotations(self, cache_dir: Path) -> Dict:
        """Download and cache COCO annotations"""
        cache_dir.mkdir(parents=True, exist_ok=True)
        annotations_file = cache_dir / "instances_val2017.json"
        
        if annotations_file.exists():
            print(f"Loading cached annotations from {annotations_file}")
            with open(annotations_file) as f:
                return json.load(f)
        
        print("Downloading COCO annotations...")
        response = await self.session.get(self.ANNOTATIONS_URL)
        response.raise_for_status()
        
        # Extract annotations from zip
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            # Find the instances file
            for name in zf.namelist():
                if 'instances_val2017.json' in name:
                    with zf.open(name) as f:
                        annotations = json.load(f)
                        # Cache for future use
                        with open(annotations_file, 'w') as out:
                            json.dump(annotations, out)
                        return annotations
        
        raise ValueError("Could not find instances_val2017.json in annotations zip")
    
    async def seed(self, count: int, cache_dir: str = "./data/coco", **kwargs) -> List[Dict]:
        """Seed COCO images"""
        cache_path = Path(cache_dir)
        
        # Download annotations
        annotations = await self.download_annotations(cache_path)
        
        # Get image list
        images = annotations['images'][:count]
        
        print(f"Seeding {len(images)} images from COCO val2017...")
        
        results = []
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(10)
        
        async def ingest_with_limit(img_info):
            async with semaphore:
                image_url = f"{self.IMAGES_BASE_URL}/{img_info['file_name']}"
                metadata = {
                    "dataset": "coco",
                    "coco_id": img_info['id'],
                    "license": img_info.get('license'),
                    "flickr_url": img_info.get('flickr_url'),
                    "date_captured": img_info.get('date_captured')
                }
                return await self.ingest_image(image_url, metadata)
        
        tasks = [ingest_with_limit(img) for img in images]
        
        # Use tqdm for progress bar
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Ingesting"):
            result = await coro
            if result:
                results.append(result)
        
        print(f"Successfully ingested {len(results)}/{len(images)} images")
        return results


class UnsplashSeeder(DatasetSeeder):
    """Seeds images from Unsplash API"""
    
    RANDOM_URL = "https://api.unsplash.com/photos/random"
    
    def __init__(self, api_url: str, api_key: str):
        super().__init__(api_url)
        self.api_key = api_key
    
    async def seed(self, count: int, **kwargs) -> List[Dict]:
        """Seed random Unsplash images"""
        if not self.api_key:
            raise ValueError("Unsplash API key required. Get one at https://unsplash.com/developers")
        
        print(f"Seeding {count} images from Unsplash...")
        
        results = []
        semaphore = asyncio.Semaphore(5)  # Lower concurrency for API rate limits
        
        async def fetch_and_ingest():
            async with semaphore:
                try:
                    # Get random image from Unsplash
                    response = await self.session.get(
                        self.RANDOM_URL,
                        headers={"Authorization": f"Client-ID {self.api_key}"},
                        params={"orientation": "landscape"}
                    )
                    response.raise_for_status()
                    photo = response.json()
                    
                    # Extract metadata
                    metadata = {
                        "dataset": "unsplash",
                        "unsplash_id": photo['id'],
                        "photographer": photo['user']['name'],
                        "photographer_url": photo['user']['links']['html'],
                        "description": photo.get('description') or photo.get('alt_description'),
                        "license": "Unsplash License",
                        "attribution_required": True
                    }
                    
                    # Use regular quality image (not raw)
                    image_url = photo['urls']['regular']
                    
                    return await self.ingest_image(image_url, metadata)
                except Exception as e:
                    print(f"Error fetching from Unsplash: {e}")
                    return None
        
        tasks = [fetch_and_ingest() for _ in range(count)]
        
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Ingesting"):
            result = await coro
            if result:
                results.append(result)
            await asyncio.sleep(0.1)  # Rate limiting
        
        print(f"Successfully ingested {len(results)}/{count} images")
        return results


class Flickr30kSeeder(DatasetSeeder):
    """Seeds images from Flickr30k dataset (requires Kaggle download)"""
    
    async def seed(self, count: int, data_dir: str = "./data/flickr30k", **kwargs) -> List[Dict]:
        """Seed Flickr30k images from local directory"""
        data_path = Path(data_dir)
        images_dir = data_path / "flickr30k_images"
        
        if not images_dir.exists():
            raise ValueError(
                f"Flickr30k images not found at {images_dir}.\n"
                "Download from: kaggle datasets download -d adityajn105/flickr30k"
            )
        
        # Get list of image files
        image_files = list(images_dir.glob("*.jpg"))[:count]
        
        print(f"Seeding {len(image_files)} images from Flickr30k...")
        
        results = []
        semaphore = asyncio.Semaphore(10)
        
        async def ingest_file(img_path):
            async with semaphore:
                try:
                    # Read image file
                    with open(img_path, 'rb') as f:
                        files = {'file': (img_path.name, f, 'image/jpeg')}
                        response = await self.session.post(
                            f"{self.api_url}/images",
                            files=files
                        )
                        response.raise_for_status()
                        result = response.json()
                        result["metadata"] = {
                            "dataset": "flickr30k",
                            "filename": img_path.name,
                            "license": "CC BY-NC-SA 2.0"
                        }
                        return result
                except Exception as e:
                    print(f"Error ingesting {img_path.name}: {e}")
                    return None
        
        tasks = [ingest_file(img) for img in image_files]
        
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Ingesting"):
            result = await coro
            if result:
                results.append(result)
        
        print(f"Successfully ingested {len(results)}/{len(image_files)} images")
        return results


def list_datasets():
    """List available datasets"""
    print("\nAvailable datasets:")
    print("\n1. COCO (2017 Validation Set)")
    print("   - ~5000 images with annotations")
    print("   - Automatic download")
    print("   - License: CC BY 4.0")
    print("   - Usage: --dataset coco --count 1000")
    
    print("\n2. Unsplash")
    print("   - High-quality photos")
    print("   - Requires API key (free)")
    print("   - License: Unsplash License (free to use)")
    print("   - Get key: https://unsplash.com/developers")
    print("   - Usage: --dataset unsplash --count 500 --api-key YOUR_KEY")
    
    print("\n3. Flickr30k")
    print("   - 30,000 images with captions")
    print("   - Requires manual download from Kaggle")
    print("   - License: CC BY-NC-SA 2.0")
    print("   - Download: kaggle datasets download -d adityajn105/flickr30k")
    print("   - Usage: --dataset flickr30k --count 1000 --data-dir ./data/flickr30k")
    print()


async def main():
    parser = argparse.ArgumentParser(description="Seed ImageSearch with dataset images")
    parser.add_argument("--dataset", choices=["coco", "unsplash", "flickr30k"], 
                       help="Dataset to seed from")
    parser.add_argument("--count", type=int, default=100,
                       help="Number of images to seed (default: 100)")
    parser.add_argument("--api-url", default="http://localhost:8000",
                       help="API URL (default: http://localhost:8000)")
    parser.add_argument("--api-key", help="API key (required for Unsplash)")
    parser.add_argument("--cache-dir", default="./data/coco",
                       help="Cache directory for COCO (default: ./data/coco)")
    parser.add_argument("--data-dir", default="./data/flickr30k",
                       help="Data directory for Flickr30k (default: ./data/flickr30k)")
    parser.add_argument("--list", action="store_true",
                       help="List available datasets")
    parser.add_argument("--output", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    if args.list:
        list_datasets()
        return
    
    if not args.dataset:
        parser.print_help()
        print("\nUse --list to see available datasets")
        return
    
    # Create seeder
    if args.dataset == "coco":
        async with COCOSeeder(args.api_url) as seeder:
            results = await seeder.seed(args.count, cache_dir=args.cache_dir)
    elif args.dataset == "unsplash":
        if not args.api_key:
            print("ERROR: Unsplash requires --api-key")
            print("Get a free key at: https://unsplash.com/developers")
            sys.exit(1)
        async with UnsplashSeeder(args.api_url, args.api_key) as seeder:
            results = await seeder.seed(args.count)
    elif args.dataset == "flickr30k":
        async with Flickr30kSeeder(args.api_url) as seeder:
            results = await seeder.seed(args.count, data_dir=args.data_dir)
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    
    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())

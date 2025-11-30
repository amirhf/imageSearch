import asyncio
import json
import os
import signal
import logging
from redis import asyncio as aioredis
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("worker")

class BaseWorker(ABC):
    def __init__(self, queue_name: str, concurrency: int = 1):
        self.queue_name = queue_name
        self.concurrency = concurrency
        self.redis = None
        self.running = False
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    async def start(self):
        """Start the worker"""
        logger.info(f"Starting {self.__class__.__name__} on queue {self.queue_name} with concurrency {self.concurrency}")
        
        # Connect to Redis
        self.redis = await aioredis.from_url(self.redis_url)
        self.running = True
        
        # Handle shutdown signals
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        # Start worker pool
        workers = [
            asyncio.create_task(self._worker_loop(i))
            for i in range(self.concurrency)
        ]
        
        try:
            await asyncio.gather(*workers)
        except asyncio.CancelledError:
            logger.info("Worker tasks cancelled")
        finally:
            await self.redis.close()
            logger.info("Worker stopped")

    async def stop(self):
        """Stop the worker gracefully"""
        logger.info("Stopping worker...")
        self.running = False

    async def _worker_loop(self, worker_id: int):
        """Main loop for each worker task"""
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Blocking pop from queue (timeout allows checking self.running)
                result = await self.redis.brpop(self.queue_name, timeout=2)
                
                if result is None:
                    continue
                
                _, job_data = result
                job = json.loads(job_data)
                
                logger.info(f"Worker {worker_id} processing job {job.get('job_id')}")
                await self.process_job(job)
                logger.info(f"Worker {worker_id} completed job {job.get('job_id')}")
                
            except Exception as e:
                if self.running:
                    logger.error(f"Worker {worker_id} error: {e}")
                    await asyncio.sleep(1)

    @abstractmethod
    async def process_job(self, job: dict):
        """Process a single job. Must be implemented by subclasses."""
        pass

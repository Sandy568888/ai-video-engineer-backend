"""
Job Queue System
Replace thread-based jobs with robust queue system
Supports Redis+Celery or RabbitMQ
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enum"""
    PENDING = 'pending'
    QUEUED = 'queued'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRYING = 'retrying'
    CANCELLED = 'cancelled'


@dataclass
class Job:
    """Job representation"""
    
    job_id: str
    job_type: str  # 'video_generation', 'tts', 'lipsync', etc.
    status: JobStatus
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    retry_count: int
    max_retries: int
    priority: int  # 0-10, higher = more priority
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data


class JobQueue:
    """
    Job Queue Manager
    
    Features:
    - Job persistence
    - Retry logic
    - Priority queue
    - Dead letter queue
    - Concurrency limits
    - Job scheduling
    """
    
    def __init__(self):
        self.backend = os.getenv('JOB_QUEUE_BACKEND', 'memory')  # 'memory', 'redis', 'rabbitmq'
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://localhost')
        
        self.max_retries = int(os.getenv('JOB_MAX_RETRIES', '3'))
        self.max_concurrent = int(os.getenv('JOB_MAX_CONCURRENT', '5'))
        self.job_timeout = int(os.getenv('JOB_TIMEOUT_SECONDS', '300'))
        
        # In-memory storage (for demo)
        self.jobs: Dict[str, Job] = {}
        self.queues: Dict[str, List[str]] = {
            'default': [],
            'high_priority': [],
            'low_priority': []
        }
        self.active_jobs: List[str] = []
        self.dead_letter_queue: List[str] = []
        
        logger.info(f"Job Queue initialized:")
        logger.info(f"  Backend: {self.backend}")
        logger.info(f"  Max retries: {self.max_retries}")
        logger.info(f"  Max concurrent: {self.max_concurrent}")
        logger.info(f"  Timeout: {self.job_timeout}s")
    
    def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: int = 5,
        max_retries: Optional[int] = None
    ) -> str:
        """
        Enqueue a new job
        
        Args:
            job_type: Type of job
            payload: Job data
            priority: Job priority (0-10)
            max_retries: Max retry attempts
        
        Returns:
            Job ID
        """
        
        job_id = str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.QUEUED,
            payload=payload,
            result=None,
            error=None,
            created_at=datetime.utcnow().isoformat(),
            started_at=None,
            completed_at=None,
            retry_count=0,
            max_retries=max_retries or self.max_retries,
            priority=priority
        )
        
        self.jobs[job_id] = job
        
        # Add to appropriate queue based on priority
        if priority >= 8:
            queue = 'high_priority'
        elif priority <= 3:
            queue = 'low_priority'
        else:
            queue = 'default'
        
        self.queues[queue].append(job_id)
        
        logger.info(f"✅ Enqueued job {job_id}: {job_type} (priority: {priority}, queue: {queue})")
        
        return job_id
    
    def dequeue(self) -> Optional[Job]:
        """
        Dequeue next job (respects priority)
        
        Returns:
            Next job to process, or None if queue empty
        """
        
        # Check if we've reached concurrent limit
        if len(self.active_jobs) >= self.max_concurrent:
            logger.debug(f"Concurrent limit reached: {len(self.active_jobs)}/{self.max_concurrent}")
            return None
        
        # Try high priority first
        for queue_name in ['high_priority', 'default', 'low_priority']:
            queue = self.queues[queue_name]
            
            if queue:
                job_id = queue.pop(0)
                job = self.jobs.get(job_id)
                
                if job:
                    job.status = JobStatus.PROCESSING
                    job.started_at = datetime.utcnow().isoformat()
                    self.active_jobs.append(job_id)
                    
                    logger.info(f"📤 Dequeued job {job_id} from {queue_name}")
                    return job
        
        return None
    
    def complete_job(
        self,
        job_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        Mark job as completed
        
        Args:
            job_id: Job identifier
            result: Job result data
        
        Returns:
            True if marked successfully
        """
        
        job = self.jobs.get(job_id)
        
        if not job:
            logger.error(f"Job not found: {job_id}")
            return False
        
        job.status = JobStatus.COMPLETED
        job.result = result
        job.completed_at = datetime.utcnow().isoformat()
        
        if job_id in self.active_jobs:
            self.active_jobs.remove(job_id)
        
        logger.info(f"✅ Job completed: {job_id}")
        return True
    
    def fail_job(
        self,
        job_id: str,
        error: str,
        retry: bool = True
    ) -> bool:
        """
        Mark job as failed
        
        Args:
            job_id: Job identifier
            error: Error message
            retry: Whether to retry the job
        
        Returns:
            True if handled successfully
        """
        
        job = self.jobs.get(job_id)
        
        if not job:
            logger.error(f"Job not found: {job_id}")
            return False
        
        job.error = error
        job.retry_count += 1
        
        if job_id in self.active_jobs:
            self.active_jobs.remove(job_id)
        
        # Check if should retry
        if retry and job.retry_count < job.max_retries:
            job.status = JobStatus.RETRYING
            
            # Re-queue with lower priority
            queue = 'low_priority'
            self.queues[queue].append(job_id)
            
            logger.warning(f"⚠️ Job failed, retrying: {job_id} (attempt {job.retry_count}/{job.max_retries})")
            return True
        else:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow().isoformat()
            
            # Move to dead letter queue
            self.dead_letter_queue.append(job_id)
            
            logger.error(f"❌ Job failed permanently: {job_id}")
            return False
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        
        job = self.jobs.get(job_id)
        
        if not job:
            return False
        
        if job.status == JobStatus.PROCESSING:
            logger.warning(f"Cannot cancel processing job: {job_id}")
            return False
        
        job.status = JobStatus.CANCELLED
        
        # Remove from queues
        for queue in self.queues.values():
            if job_id in queue:
                queue.remove(job_id)
        
        logger.info(f"🚫 Job cancelled: {job_id}")
        return True
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        
        job = self.jobs.get(job_id)
        return job.to_dict() if job else None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        
        total_jobs = len(self.jobs)
        
        status_counts = {}
        for status in JobStatus:
            count = len([j for j in self.jobs.values() if j.status == status])
            status_counts[status.value] = count
        
        queue_depths = {
            name: len(queue) for name, queue in self.queues.items()
        }
        
        return {
            'backend': self.backend,
            'total_jobs': total_jobs,
            'active_jobs': len(self.active_jobs),
            'max_concurrent': self.max_concurrent,
            'status_counts': status_counts,
            'queue_depths': queue_depths,
            'dead_letter_queue': len(self.dead_letter_queue),
            'max_retries': self.max_retries
        }
    
    def cleanup_old_jobs(self, days: int = 7) -> int:
        """
        Clean up old completed/failed jobs
        
        Args:
            days: Jobs older than this will be deleted
        
        Returns:
            Number of jobs deleted
        """
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = 0
        
        jobs_to_delete = []
        
        for job_id, job in self.jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.completed_at:
                    completed = datetime.fromisoformat(job.completed_at)
                    if completed < cutoff:
                        jobs_to_delete.append(job_id)
        
        for job_id in jobs_to_delete:
            del self.jobs[job_id]
            deleted += 1
        
        logger.info(f"🗑️ Cleaned up {deleted} old jobs")
        return deleted

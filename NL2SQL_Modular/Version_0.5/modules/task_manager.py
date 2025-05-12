"""
Task Manager for handling background operations
"""

import threading
from queue import Queue
import time
from typing import Callable, Any, Dict, List, Optional
import uuid
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task:
    def __init__(self, func: Callable, args: List = None, kwargs: Dict = None, 
                 callback: Callable = None):
        self.id = str(uuid.uuid4())
        self.func = func
        self.args = args or []
        self.kwargs = kwargs or {}
        self.callback = callback
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.progress = 0
        self.start_time = None
        self.end_time = None
        
    def execute(self):
        """Execute the task function"""
        try:
            self.status = TaskStatus.RUNNING
            self.start_time = time.time()
            
            self.result = self.func(*self.args, **self.kwargs)
            self.status = TaskStatus.COMPLETED
        except Exception as e:
            self.error = str(e)
            self.status = TaskStatus.FAILED
        finally:
            self.end_time = time.time()
            
            # Execute callback if provided
            if self.callback:
                try:
                    self.callback(self)
                except Exception as e:
                    print(f"Error in callback: {e}")

class TaskManager:
    """Manager for background tasks"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.task_queue = Queue()
        self.tasks = {}
        self.workers = []
        self.worker_count = 3
        self.running = True
        self._start_workers()
        self._initialized = True
    
    def _worker(self):
        """Worker thread that processes tasks from the queue"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                task.execute()
                self.task_queue.task_done()
            except Exception:
                # Queue.get timeout, just continue
                pass
    
    def _start_workers(self):
        """Start worker threads"""
        for _ in range(self.worker_count):
            worker = threading.Thread(target=self._worker)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def add_task(self, func: Callable, args: List = None, kwargs: Dict = None, 
                callback: Callable = None) -> str:
        """Add a task to the queue"""
        task = Task(func, args, kwargs, callback)
        self.tasks[task.id] = task
        self.task_queue.put(task)
        return task.id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            return True
        return False
    
    def shutdown(self):
        """Shutdown the task manager"""
        self.running = False
        # Wait for all workers to finish
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=0.5)

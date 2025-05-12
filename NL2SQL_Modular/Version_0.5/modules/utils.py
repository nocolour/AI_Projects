import os
import logging
from datetime import datetime
import traceback
import threading
from functools import wraps

def setup_logging():
    """Setup logging with daily log files in logging directory"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logging")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_date = datetime.now().strftime("%Y-%m-%d")
    log_filename = os.path.join(log_dir, f"error_{log_date}.log")
    logging.basicConfig(
        filename=log_filename,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return log_dir

def setup_tmp_dir():
    """Setup tmp directory for configuration and encryption files"""
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tmp")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    return tmp_dir

def log_exception(prefix, e):
    """Log an exception with traceback"""
    error_msg = f"{prefix}: {str(e)}"
    logging.error(f"{error_msg}\n{traceback.format_exc()}")
    return error_msg

def run_in_thread(func):
    """Decorator to run a function in a separate thread"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

def timed_lru_cache(seconds=600, maxsize=128):
    """LRU cache that expires after specified seconds"""
    def decorator(func):
        # Use functools.lru_cache for the actual caching
        import functools
        from datetime import datetime, timedelta
        
        # Store the time when each result was cached
        cache_timestamps = {}
        
        @functools.lru_cache(maxsize=maxsize)
        def cached_func(*args, **kwargs):
            return func(*args, **kwargs)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if result is cached and not expired
            key = hash((args, frozenset(kwargs.items())))
            now = datetime.now()
            
            if key in cache_timestamps:
                if now - cache_timestamps[key] < timedelta(seconds=seconds):
                    return cached_func(*args, **kwargs)
                else:
                    # Expire the cache for this key
                    cached_func.cache_clear()
            
            # Cache the result and timestamp
            result = cached_func(*args, **kwargs)
            cache_timestamps[key] = now
            return result
            
        # Add method to clear cache
        wrapper.cache_clear = cached_func.cache_clear
        wrapper.cache_info = cached_func.cache_info
        
        return wrapper
    return decorator

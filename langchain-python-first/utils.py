import time

def log_execution_duration(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        print(f"{func.__name__} completed in {duration:.2f} seconds.")
        return result
    return wrapper

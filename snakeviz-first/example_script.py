import time

def slow_function():
    time.sleep(2)  # Simulates a slow operation

def fast_function():
    return 1

def main():
    for _ in range(3):
        slow_function()
        fast_function()

if __name__ == "__main__":
    main()

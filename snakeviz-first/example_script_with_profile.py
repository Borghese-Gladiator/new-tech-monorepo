import cProfile
import pstats
from io import StringIO
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
    # Create a profiler instance
    profiler = cProfile.Profile()

    # Start profiling
    profiler.enable()

    # Code block to profile
    main()

    # Stop profiling
    profiler.disable()

    # Save profiling results to a file
    with open("profile_output.prof", "w") as f:
        ps = pstats.Stats(profiler, stream=f)
        ps.strip_dirs().sort_stats("cumulative").print_stats()

    print("Profile data has been saved to 'profile_output.prof'.")
    print("Run `snakeviz profile_output.prof` to visualize.")

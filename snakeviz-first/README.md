# SnakeViz
SnakeViz is graphical viewer for Python's built-in profiler outputs (`cProfile`). Since `cProfile` records information about function calls, execution times, and more, SnakeViz can display this info as a **call stack graph** in your web browser.


## Usage
profile code and save output to profile file (`*.prof`)
```
# run script with cProfile output
python -m cProfile -o profile_output.prof example_script.py

# run script with code to build cProfile output
python example_script_with_profile.py
```

visualize profile file (`*.prof`)
```
snakeviz profile_output.prof
```

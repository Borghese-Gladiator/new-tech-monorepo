#===========================
#   Currying
#===========================
#  transform function that takes multiple arguments into a sequence of functions that each take a single argument

# A regular function
def add(x, y):
    return x + y

# A curried version of the add function
def curried_add(x):
    def add_y(y):
        return x + y
    return add_y

# Usage
add_5 = curried_add(5)  # Partially applies x = 5
print(add_5(3))         # 8
print(add_5(10))        # 15

# example
from functools import partial


def multiply(x, y):
    return x * y

multiply_by_2 = partial(multiply, 2)  # Fix x = 2
print(multiply_by_2(5))              # 10

#===========================
#  Partial Application
#===========================
def power(base, exponent):
    return base ** exponent

# Partially apply the base
square = partial(power, exponent=2)
cube = partial(power, exponent=3)

print(square(4))  # 16
print(cube(2))    # 8

#---------------------------------------------------------------------------------------

#===========================
#  FP Basics
#===========================
# Pure function: depends only on input arguments
def add(x, y):
    return x + y

# NOT Pure: modifies state outside its scope
total = 0
def add_to_total(x):
    global total
    total += x
    return total

# Immutability
original_list = [1, 2, 3]
new_list = original_list + [4]  # Creates a new list
print(original_list)  # [1, 2, 3]
print(new_list)       # [1, 2, 3, 4]

# First Class and Higher Order functions
def square(x):
    return x * x

def apply_function(func, value):
    return func(value)

print(apply_function(square, 5))  # 25

# Recursion for iteration
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

print(factorial(5))  # 120

# Function Composition
def multiply_by_two(x):
    return x * 2

def add_three(x):
    return x + 3

def compose(f, g):
    return lambda x: f(g(x))

new_function = compose(multiply_by_two, add_three)
print(new_function(5))  # (5 + 3) * 2 = 16

from functools import reduce


def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)

composed = compose(multiply_by_two, square)
print(composed(5))  # 5^2 * 2 = 50

# MAP, FILTER, REDUCE - higher order functions
numbers = [1, 2, 3, 4, 5]

# Imperative approach (how to do it)
squared_numbers = []
for num in numbers:
    squared_numbers.append(num ** 2)

# Declarative approach (what to do)
squared_numbers_fp = list(map(lambda x: x ** 2, numbers))

print(squared_numbers)      # [1, 4, 9, 16, 25]
print(squared_numbers_fp)   # [1, 4, 9, 16, 25]

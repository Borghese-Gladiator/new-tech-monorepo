#===========================
#   Monads
#===========================
# manage side effects by structuring computations while maintaining purity

class Maybe:
    def __init__(self, value):
        self.value = value

    def bind(self, func):
        if self.value is None:
            return Maybe(None)
        return Maybe(func(self.value))

# Usage
result = Maybe(5).bind(lambda x: x * 2).bind(lambda x: x + 3)
print(result.value)  # 13

none_result = Maybe(None).bind(lambda x: x * 2)
print(none_result.value)  # None

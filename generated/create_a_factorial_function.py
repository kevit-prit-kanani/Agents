def factorial(n):
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("factorial() only accepts non-negative integers")
    if n < 0:
        raise ValueError("factorial() is not defined for negative integers")

    result = 1
    for i in range(2, n + 1):
        result *= i

    return result

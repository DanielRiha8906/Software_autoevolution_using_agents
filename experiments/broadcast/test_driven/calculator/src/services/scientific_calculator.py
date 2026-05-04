import math

from .calculator import Calculator


class ScientificCalculator(Calculator):
    """A scientific calculator that extends basic Calculator with trigonometric and logarithmic functions."""

    def sin(self, x: float) -> float:
        """Compute the sine of x (in radians)."""
        return math.sin(x)

    def cos(self, x: float) -> float:
        """Compute the cosine of x (in radians)."""
        return math.cos(x)

    def tan(self, x: float) -> float:
        """Compute the tangent of x (in radians)."""
        return math.tan(x)

    def log(self, x: float) -> float:
        """Compute the logarithm base 10 of x. Raises Exception for non-positive input."""
        if x <= 0:
            raise Exception("Logarithm is undefined for non-positive numbers")
        return math.log10(x)

    def ln(self, x: float) -> float:
        """Compute the natural logarithm of x."""
        return math.log(x)

    def exp(self, x: float) -> float:
        """Compute e raised to the power of x."""
        return math.exp(x)

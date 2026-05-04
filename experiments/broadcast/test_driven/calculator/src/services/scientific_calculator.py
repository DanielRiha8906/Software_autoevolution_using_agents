"""Scientific calculator service.

Extends the basic calculation engine with trigonometric and logarithmic
functions while maintaining the core layer separation.
"""

import math

from ..core.calculation_engine import BasicCalculationEngine


class ScientificCalculator(BasicCalculationEngine):
    """A scientific calculator that extends basic calculator functionality.

    Adds trigonometric and logarithmic functions while inheriting all
    basic arithmetic operations from the core calculation engine.
    """

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
        """Compute the logarithm base 10 of x.

        Args:
            x: The input value (must be positive)

        Returns:
            The base-10 logarithm of x

        Raises:
            Exception: If x is non-positive
        """
        if x <= 0:
            raise Exception("Logarithm is undefined for non-positive numbers")
        return math.log10(x)

    def ln(self, x: float) -> float:
        """Compute the natural logarithm of x.

        Args:
            x: The input value

        Returns:
            The natural logarithm of x
        """
        return math.log(x)

    def exp(self, x: float) -> float:
        """Compute e raised to the power of x.

        Args:
            x: The exponent

        Returns:
            e^x
        """
        return math.exp(x)

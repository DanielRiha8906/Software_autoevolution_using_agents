"""Calculator service - delegates to calculation engine.

This module provides backward compatibility for the existing Calculator
class by delegating to the core calculation engine.
"""

from ..core.calculation_engine import BasicCalculationEngine
from ..models.operation import Operation


class Calculator(BasicCalculationEngine):
    """Legacy Calculator class that delegates to BasicCalculationEngine.

    Provides backward compatibility while allowing the pure calculation
    logic to be housed in the core.calculation_engine module.
    """
    pass

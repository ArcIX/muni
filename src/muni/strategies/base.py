from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """The interface that all strategies must implement."""
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """This method must be overridden by subclasses."""
        pass
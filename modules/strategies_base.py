from abc import ABC, abstractmethod

class MACD(ABC):
    @abstractmethod
    def get_data(self):
        pass

    @abstractmethod
    def get_indicators(self):
        pass

    @abstractmethod
    def execute_strat(self):
        pass
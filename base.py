# Base class

from abc import ABC, abstractmethod
import logging

class PipelineStage(ABC):
    # For classes that take data in and return data

    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)

        @abstractmethod
        def run(self, data=None):
            ...

            
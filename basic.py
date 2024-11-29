from abc import ABC, abstractmethod


class ServiceInterface(ABC):

    def __init__(self):
        self.service = self.setup()

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def generate_content(self, instruction, conversation):
        pass

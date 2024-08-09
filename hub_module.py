from abc import ABC, abstractmethod


class HubModule(ABC):
    """Hub modules should implement this class. Any specialized feature or screen should be
    a hub module, e.g. spotipy, debug pin panel, even the i2c controller. If it doesnt need to draw it can just pass it
    """

    @abstractmethod
    def update_step(self):
        """input processing and data updates should happen here"""
        pass

    @abstractmethod
    def draw_step(self):
        """any drawing activity should happen here. the Hub can call it during its texture
        step or its draw step"""
        pass

    @abstractmethod
    def debug_step(self):
        """Any debug information is drawn or printed here, if enabled"""
        pass

from abc import ABC, abstractmethod


class MotorDriverInterface(ABC):
    """
    An interface for controlling a motor.
    """

    @abstractmethod
    def __init__(self):
        """Initializes the motor driver and sets default values."""
        pass

    @abstractmethod
    def get_pos(self):
        """
        Returns the current position of the motor.
        Should be interpreted as (x, y) coordinates.
        """
        pass

    @abstractmethod
    def abs_move(self, x: float, y: float):
        """Moves the motor to the specified position in absolute coordinates.

        Args:
            x (float): The desired x position.
            y (float): The desired y position.
        """
        pass

    @abstractmethod
    def rel_move(self, dx: float, dy: float):
        """Moves the motor to the specified position in relative coordinates.

        Args:
            dx (float): The desired change in x position.
            dy (float): The desired change in y position.
        """
        pass

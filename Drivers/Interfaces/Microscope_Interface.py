from abc import ABC, abstractmethod


class MicroscopeDriverInterface(ABC):
    """
    An interface for controlling a microscope.
    """

    @abstractmethod
    def __init__(self):
        """
        Initializes the microscope driver and sets default values.
        """
        pass

    @abstractmethod
    def lamp_on(self):
        """
        Turns on the microscope's lamp.
        """
        pass

    @abstractmethod
    def lamp_off(self):
        """
        Turns off the microscope's lamp.
        """
        pass

    @abstractmethod
    def rotate_nosepiece_forward(self):
        """
        Rotates the microscope's nosepiece forward.
        """
        pass

    @abstractmethod
    def rotate_nosepiece_backward(self):
        """
        Rotates the microscope's nosepiece backward.
        """
        pass

    @abstractmethod
    def set_lamp_voltage(self, voltage: float):
        """
        Sets the voltage of the microscope's lamp.

        Args:
            voltage (float): The desired voltage for the lamp.
        """
        pass

    @abstractmethod
    def set_mag(self, mag_idx: int):
        """
        Sets the position of the microscope's nosepiece and automatically sets the height.

        Args:
            mag_idx (int): The desired nosepiece position (between 1 and 5).
        """
        pass

    @abstractmethod
    def set_lamp_aperture_stop(self, aperture_stop: float):
        """
        Sets the aperture stop of the microscope's lamp.

        Args:
            aperture_stop (float): The desired aperture stop for the lamp.
        """
        pass

    @abstractmethod
    def get_properties(self):
        """
        Fetches and returns the current properties of the microscope.

        Returns:
            dict: A dictionary containing the current properties of the microscope, including nosepiece position,
            lamp aperture, and lamp voltage.
        """
        pass

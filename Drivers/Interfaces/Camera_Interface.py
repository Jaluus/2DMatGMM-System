from abc import ABC, abstractmethod


class CameraDriverInterface(ABC):
    """
    An interface for a microscope camera driver.
    """

    @abstractmethod
    def __init__(self):
        """
        Initializes the camera driver.
        """
        pass

    @abstractmethod
    def set_properties(
        self,
        exposure: float = None,
        gain: int = None,
        white_balance: tuple = None,
        gamma: int = None,
    ):
        """
        Sets the properties of the camera.

        Args:
            exposure (float, optional): The exposure time of the camera in seconds. Defaults to None.
            gain (int, optional): The gain of the image. A value of 0 means normal gain. Defaults to None.
            white_balance (tuple, optional): The RGB white balance of the camera as a tuple (e.g., (64,64,64)). Defaults to None.
            gamma (int, optional): The gamma of the image, where a value of 120 implies a gamma of 1.2. Defaults to None.
        """
        pass

    @abstractmethod
    def get_properties(self):
        """
        Fetches and returns the current properties of the camera.

        Returns:
            dict: A dictionary containing the current properties of the camera. Includes 'gain', 'exposure',
            'gamma', 'white_balance', and 'time'.
        """
        pass

    @abstractmethod
    def get_image(self):
        """
        Captures and returns an image from the camera.

        Returns:
            ndarray: The captured image.
        """
        pass

    @abstractmethod
    def stop_camera(self):
        """
        Stops the operation of the camera.
        """
        pass

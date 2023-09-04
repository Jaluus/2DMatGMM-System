from Drivers.Interfaces.Camera_Interface import CameraDriverInterface
import Drivers.Camera_Driver.tisgrabber.tisgrabber as IC
import cv2
import numpy as np
import time


class CameraDriver(CameraDriverInterface):
    """
    eays to use microscope cam class
    """

    def __init__(
        self,
        cam_name="DFK 33UX174 38020321",
        NULL_R=14,
        NULL_G=14,
        NULL_B=14,
    ):
        self.camera = self.__init_camera(cam_name)

        self.null_image = np.full(
            (1200, 1920, 3), np.array([NULL_B, NULL_G, NULL_R], dtype=np.uint8)
        )

        self.DEFAULT_PROPERTIES = {
            1: {
                "exposure": 0.07,
                "gain": 0,
                "white_balance": (127, 64, 90),
                "gamma": 100,
            },
            2: {
                "exposure": 0.07,
                "gain": 0,
                "white_balance": (127, 64, 90),
                "gamma": 100,
            },
            3: {
                "exposure": 0.07,
                "gain": 0,
                "white_balance": (127, 64, 90),
                "gamma": 100,
            },
            4: {
                "exposure": 0.07,
                "gain": 0,
                "white_balance": (127, 64, 90),
                "gamma": 100,
            },
            5: {
                "exposure": 0.03,
                "gain": 100,
                "white_balance": (127, 64, 90),
                "gamma": 100,
            },
        }

    def __init_camera(self, cam_name):
        """
        Initiates the Camera Object and starts the Live Video\nreturns the Camera Object
        """
        # About 0.84 seconds per init
        # sometime 10.4 seconds

        # Create the camera object.
        Camera = IC.TIS_CAM()

        # Open a device with hard coded unique name:
        Camera.open(cam_name)

        # checks it the cam exists
        if Camera.IsDevValid() != 1:
            print(f"No device found with the name {cam_name}, Choose Camera : ")
            Camera.ShowDeviceSelectionDialog()

        # Set a video format
        Camera.SetVideoFormat("RGB24 (1920x1200)")

        # Set a frame rate
        Camera.SetFrameRate(13.5)

        # Start the live video stream, but show no own live video window. We will use OpenCV for this.
        Camera.StartLive(0)
        return Camera

    def set_new_null_image(self, NULL_R, NULL_G, NULL_B):
        self.null_image = np.full(
            (1200, 1920, 3), np.array([NULL_B, NULL_G, NULL_R], dtype=np.uint8)
        )

    def get_camera(self):
        return self.camera

    def set_default_properties(self, magnification: int):
        """set default properties for each magnifiaction

        Args:
            magnification (int): Number between 1 and 5
            - 1 : 2.5x
            - 2 : 5x
            - 3 : 20x
            - 4 : 50x
            - 5 : 100x
        """
        try:
            self.set_properties(**self.DEFAULT_PROPERTIES[magnification])
        except KeyError as keyerror:
            print("Wrong Magnification Number")
        except OSError as oserror:
            print(oserror)

    def set_properties(
        self,
        exposure: float = None,
        gain: int = None,
        white_balance: tuple = None,
        gamma: int = None,
    ):
        """
        Sets camera values\n
        exposure is given in seconds\n
        gain is given in logical Values, aka 0 is normal gain\n
        white_balance is given as a tuple like (64,64,64) for rbg balance\n
        gamma is the gamma times 100, real gamma of 1.2 would be 120 here\n
        Default values are for the 20x magnification\n
        """
        # In order to set a fixed exposure time, the Exposure Automatic must be disabled first.
        # Using the IC Imaging Control VCD Property Inspector, we know, the item is "Exposure", the
        # element is "Auto" and the interface is "Switch". Therefore we use for disabling:

        # Disable all automatic changes
        # "0" is off, "1" is on.
        # Set an absolute exposure time
        if exposure is not None:
            self.camera.SetPropertySwitch("Exposure", "Auto", 0)
            self.camera.SetPropertyAbsoluteValue("Exposure", "Value", exposure)
        if gain is not None:
            self.camera.SetPropertySwitch("Gain", "Auto", 0)
            self.camera.SetPropertyValue("Gain", "Value", gain)
        if gamma is not None:
            self.camera.SetPropertySwitch("WhiteBalance", "Auto", 0)
            self.camera.SetPropertyValue("Gamma", "Value", gamma)

        if white_balance is not None:
            self.camera.SetPropertyValue(
                "WhiteBalance", "White Balance Red", white_balance[0]
            )
            self.camera.SetPropertyValue(
                "WhiteBalance", "White Balance Green", white_balance[1]
            )
            self.camera.SetPropertyValue(
                "WhiteBalance", "White Balance Blue", white_balance[2]
            )

    def get_properties(self):
        """
        returns the current camera properties\n
        dictkeys:\n
        'gain' : the current gain, 0 means normal gain\n
        'exposure' : the current exposure time in seconds\n
        'gamma' : the gamma of the image, 120 means 1.2 etc..\n
        'white_balance' : the rgb white balance in tuple form e.g. (64,64,64)\n
        'time' : the current time as unix timestamp
        """
        val_dict = {}
        # get the Gain
        val_dict["gain"] = self.camera.GetPropertyValue("Gain", "Value")

        ExposureTime = [0]
        self.camera.GetPropertyAbsoluteValue("Exposure", "Value", ExposureTime)
        val_dict["exposure"] = ExposureTime[0]

        val_dict["gamma"] = self.camera.GetPropertyValue("Gamma", "Value")

        # Same goes with white balance. We make a complete red image:
        WBr = self.camera.GetPropertyValue("WhiteBalance", "White Balance Red")
        WBg = self.camera.GetPropertyValue("WhiteBalance", "White Balance Green")
        WBb = self.camera.GetPropertyValue("WhiteBalance", "White Balance Blue")

        val_dict["white_balance"] = (WBr, WBg, WBb)

        val_dict["time"] = time.time()

        return val_dict

    def get_image(self):
        """
        returns an image taken by the camera with the corrosponding metadata dict\n
        Subtracts the null ("DUNKELSTROM") values from the image\n

        dictkeys:\n
        'gain' : the current gain, 0 means normal gain\n
        'exposure' : the current exposure time in seconds\n
        'gamma' : the gamma of the image, 120 means 1.2 etc..\n
        'white_balance' : the rgb white balance in tuple form e.g. (64,64,64)\n
        'time' : the current time as unix timestamp
        """

        self.camera.SnapImage()
        image = self.camera.GetImage()

        # flip the image to get the correct orientation
        image = cv2.flip(image, 0)

        # Remove the null activation of the camera
        image = cv2.subtract(image, self.null_image)

        return image

    def stop_camera(self):
        self.camera.StopLive()


if __name__ == "__main__":
    cam = CameraDriver()

    import matplotlib.pyplot as plt

    img, props = cam.get_image()
    plt.imshow(img)
    print(props)
    plt.show()

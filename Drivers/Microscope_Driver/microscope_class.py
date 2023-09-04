import win32com.client
from Drivers.Interfaces.Microscope_Interface import MicroscopeDriverInterface


class MicroscopeDriver(MicroscopeDriverInterface):
    """
    an easy way to control the microscope
    """

    def __init__(self):
        # Creates an microscope object, only possible if NIS is closed and no other application is using the LV
        self.micro = win32com.client.Dispatch("Nikon.LvMic.nikonLV")
        # this line is shit, took 4 hours

        self.set_default_values()

    def set_default_values(self):
        """Sets the Default values\n
        Lamp Volatge: 6.4V\n
        Aperture: 2.3\n
        """
        self.lamp_on()
        self.set_lamp_voltage(6.4)
        self.set_lamp_aperture_stop(2.3)

    def get_microscope_object(self):
        return self.micro

    def set_z_height(self, height):
        """
        Sets the Height in µm\n
        Only works if the AF is not on\n
        Has small protection by only setting height between 3500 and 6500 µm
        """
        try:
            if 3500 < height < 6500:
                rescaled_pulses = height * 20
                self.micro.ZDrive.MoveAbsolute(rescaled_pulses)
        except:
            print("Already in Focus!")

    def get_z_height(self):
        height = self.micro.ZDrive.Value()
        return height

    def lamp_on(self):
        self.micro.EpiLamp.On()

    def lamp_off(self):
        self.micro.EpiLamp.Off()

    def rotate_nosepiece_forward(self):
        self.micro.Nosepiece.Forward()

    def rotate_nosepiece_backward(self):
        self.micro.Nosepiece.Reverse()

    def set_lamp_voltage(self, voltage: float):
        self.micro.EpiLamp.Voltage = voltage

    def set_mag(self, mag_idx: int):
        """
        Swaps the Position of the Nosepiece\n
        Automatically sets the Height\n
        1 : 2.5x 5500µm\n
        2 : 5x 4300µm\n
        3 : 20x 3930µm\n
        4 : 50x 3900µm\n
        5 : 100x 3900µm\n
        """
        if 0 < mag_idx < 6:
            self.micro.Nosepiece.Position = mag_idx
        else:
            print(f"Wrong Mag Idx, you gave {mag_idx}, needs to be 1 to 5")

    def set_lamp_aperture_stop(self, aperture_stop: float):
        self.micro.EpiApertureStop.ApertureStop = aperture_stop

    def get_af_status(self):
        """
        Currently Bugged\n
        Return Codes:\n
        AfStatusUnknown     : -1\n
        AfStatusJustFocus   : 1\n
        AfStatusUnderFocus  : 2\n
        AfStatusOverFocus   : 3\n
        AfStatusOutOfRange  : 9
        """
        return self.micro.ZDrive.AfStatus()

    def is_af_searching(self):
        return self.micro.ZDrive.AfSearchMode()

    def find_af(self, mode: int = 2):
        """
        There are 2 modes, 1 and 2, i dont know the difference
        """
        self.micro.ZDrive.SearchAF(0)

    def get_properties(self):
        """
        Returns the current properties of the microscope\n
        dict keys:
        'nosepiece' : positon of the nosepiece
        'aperture'  : current ApertureStop of the EpiLamp
        'voltage'   : current Voltage of the EpiLamp in Volts
        """
        val_dict = {}
        # height = self.micro.ZDrive.Value()
        #   File "C:\Users\Transfersystem User\.conda\envs\micro\lib\site-packages\win32com\client\dynamic.py", line 197, in __call__
        #     return self._get_good_object_(self._oleobj_.Invoke(*allArgs),self._olerepr_.defaultDispatchName,None)
        # pywintypes.com_error: (-2147352567, 'Exception occurred.', (0, 'Nikon.LvMic.ZDrive.1', '', None, 0, -2147352567), None)
        val_dict[
            "z_height"
        ] = -1  # self.get_z_height() This leads to errors sometimes, no idea why
        val_dict["nosepiece"] = self.micro.Nosepiece.Position()
        val_dict["aperture"] = self.micro.EpiApertureStop.ApertureStop()
        val_dict["light"] = self.micro.EpiLamp.Voltage()
        return val_dict


if __name__ == "__main__":
    micro = MicroscopeDriver()

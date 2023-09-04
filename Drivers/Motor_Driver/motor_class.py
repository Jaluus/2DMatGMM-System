import os
from Drivers.Interfaces.Motor_Interface import MotorDriverInterface
from ctypes import *
import sys

file_path = os.path.dirname(__file__)
try:
    dll_dir = os.path.join(file_path, "DLL_Files")
    dll_folders = os.listdir(dll_dir)
    dll_folder = [
        folder for folder in dll_folders if folder.startswith("TangoDLL_64bit_V")
    ][0]
except:
    raise ValueError("No Tango DLL found, Check the DLL_Files folder")

dll_path = os.path.join(dll_dir, dll_folder, "Tango_DLL.dll")


class MotorDriver(MotorDriverInterface):
    """
    controls the Tango XY Plate
    """

    def __init__(self, dll_path=dll_path):
        print(dll_path)
        self.dll_path = dll_path
        self.m_Tango = cdll.LoadLibrary(self.dll_path)

        if self.m_Tango == 0:
            print("Error: failed to load DLL")
            sys.exit(0)

        # Tango_DLL.dll loaded successfully

        if self.m_Tango.LSX_CreateLSID == 0:
            print("unexpected error. required DLL function CreateLSID() missing")
            sys.exit(0)
        # continue only if required function exists

        self.LSID = c_int()
        error = int  # value is either DLL or Tango error number if not zero
        error = self.m_Tango.LSX_CreateLSID(byref(self.LSID))
        if error > 0:
            print("Error: " + str(error))
            sys.exit(0)

        # OK: got communication ID from DLL (usually 1. may vary with multiple connections)
        # keep this LSID in mind during the whole session

        if self.m_Tango.LSX_ConnectSimple == 0:
            print("unexepcted error. required DLL function ConnectSimple() missing")
            sys.exit(0)
        # continue only if required function exists

        # error = self.m_Tango.LSX_ConnectSimple(self.LSID, 2, "COM3", 57600, 0)
        # following combination of -1,"" works only for USB but not for RS232 connections
        error = self.m_Tango.LSX_ConnectSimple(self.LSID, -1, "", 57600, 0)
        if error > 0:
            print("Error: LSX_ConnectSimple " + str(error))
            print("Try Restarting the XY-Plate, if this does not help, restart the PC")
            sys.exit(0)

        print("TANGO is now successfully connected to DLL")

        self.full_calibrate()

    def _calibrate(self):
        # calibrate all axes
        error = self.m_Tango.LSX_Calibrate(self.LSID)
        if error > 0:
            print("Error: Calibrate " + str(error))

    def get_tango_object(self):
        return self.m_Tango

    def get_LSID(self):
        return self.LSID

    def _set_dimensions(self, dim: int):
        # Get the Dimensions
        error = self.m_Tango.LSX_SetDimensions(self.LSID, dim, dim, dim, dim)
        if error > 0:
            print("Error: setDim " + str(error))
        else:
            print("LSX_setDimensions = " + str(dim))

    def get_dimensions(self):
        dimX = c_int()
        dimY = c_int()
        dimZ = c_int()
        dimA = c_int()
        # Get the Dimensions
        error = self.m_Tango.LSX_GetDimensions(
            self.LSID, byref(dimX), byref(dimY), byref(dimZ), byref(dimA)
        )
        if error > 0:
            print("Error: getDim " + str(error))
        else:
            print(
                "LSX_GetDimensions = "
                + str(dimX.value)
                + " "
                + str(dimY.value)
                + " "
                + str(dimZ.value)
                + " "
                + str(dimA.value)
            )

    def _range_measure(self):
        error = self.m_Tango.LSX_RMeasure(self.LSID)
        if error > 0:
            print("Error: RM " + str(error))

    def full_calibrate(self):
        """
        Calibrates the plant and sets the Software endstops
        """
        # Setting dimensons to mm
        # use 1 to go for mu m
        self._set_dimensions(2)
        self.get_dimensions()
        x, y = self.get_pos()
        # calibrate all axes
        print("Starting calibration...")
        self._calibrate()
        self._range_measure()
        self.abs_move(x, y)
        print("Calibration complete")

    def get_pos(self):
        """
        Returns the Current Position
        """
        # query actual position (4 axes) (unit depends on GetDimensions)
        dx = c_double()
        dy = c_double()
        dz = c_double()
        da = c_double()
        error = self.m_Tango.LSX_GetPos(
            self.LSID, byref(dx), byref(dy), byref(dz), byref(da)
        )
        if error > 0:
            print("Error: GetPos " + str(error))

        return (dx.value, dy.value)

    def abs_move(self, x, y, silent: bool = True, wait_for_finish: bool = True):
        """
        moves to an absolute position, checks for max_y and max_y\n
        """
        moveX = c_double(x)
        moveY = c_double(y)
        moveZ = c_double(0.0)
        moveA = c_double(0.0)
        wait_for_finish = c_bool(wait_for_finish)

        error = self.m_Tango.LSX_MoveAbs(
            self.LSID, moveX, moveY, moveZ, moveA, wait_for_finish
        )
        if error > 0:
            print("Error: abs_move " + str(error))
            sys.exit()
        else:
            if not silent:
                print(f"Moved to {x}, {y} (Absolut)")

    def rel_move(self, dx, dy, silent: bool = True):
        """
        moves relative to the Current position, checks for max_x and max_y\n
        returns False if the move was unsuccesful\n
        return True if successful
        """

        move_dx = c_double(dx)
        move_dy = c_double(dy)
        move_dz = c_double(0.0)
        move_da = c_double(0.0)

        error = self.m_Tango.LSX_MoveRel(
            self.LSID, move_dx, move_dy, move_dz, move_da, True
        )
        if error > 0:
            print("Error: rel_move " + str(error))
            sys.exit()
        else:
            if not silent:
                print(f"Moved by {dx}, {dy} (Rel)")
            return True

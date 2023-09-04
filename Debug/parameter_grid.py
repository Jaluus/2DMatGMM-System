import os
import cv2
import time

from Drivers.Camera_Driver.camera_class import camera_driver_class
from Drivers.Microscope_Driver.microscope_class import (
    microscope_driver_class,
)

file_path = "Path/To/Save/Location"
os.makedirs(file_path)

microscope = microscope_driver_class()
camera = camera_driver_class()

GAIN = 0
WHITE_BALANCE = (127, 64, 90)
GAMMA = 100

APERTURE_RANGE = [1.2, 2, 2.5, 3, 4, 5, 6, 7, 8, 8.5]
EXPOSURE_RANGE = [0.01 * n for n in range(1, 50, 2)]
VOLTAGE_RANGE = [n for n in range(4, 11)]

i = 0
max_i = len(APERTURE_RANGE) * len(EXPOSURE_RANGE) * len(VOLTAGE_RANGE)

for voltage in VOLTAGE_RANGE:
    microscope.set_lamp_voltage(voltage)
    time.sleep(1)

    for aperture in APERTURE_RANGE:
        microscope.set_lamp_aperture_stop(aperture)
        time.sleep(1)

        for exposure in EXPOSURE_RANGE:
            i = i + 1
            print(f"{i} / {max_i} : {i/max_i * 100:.2f}%", end="\t\r")
            camera.set_properties(
                exposure=exposure,
                gain=GAIN,
                white_balance=WHITE_BALANCE,
                gamma=GAMMA,
            )

            time.sleep(0.6)

            img = camera.get_image()

            cam_props = camera.get_properties()
            mic_props = microscope.get_properties()
            all_props = {**cam_props, **mic_props}

            picture_path = os.path.join(
                file_path,
                f"{round(all_props['light'],1):.1f}_{round(all_props['aperture'],1):.1f}_{round(all_props['exposure'],2):.2f}.png",
            )
            cv2.imwrite(picture_path, img)

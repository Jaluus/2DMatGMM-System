import os
import time

import cv2
import numpy as np

from Drivers import CameraDriver, MicroscopeDriver
from Utils.preprocessor_functions import remove_vignette_fast

file_path = os.path.dirname(os.path.abspath(__file__))
ff_path = "Path/To/The/Flatfield.png"

microscope = MicroscopeDriver()
camera = CameraDriver()

VOLTAGE = 10
APERTURE = 3
EXPOSURE = 0.1
GAIN = 0
WHITE_BALANCE = (127, 64, 90)
GAMMA = 100

MAG_KEYS = {
    1: "2.5x",
    2: "5x",
    3: "20x",
    4: "50x",
    5: "100x",
}

flatfield = cv2.imread(ff_path)
if flatfield is not None:
    flatfield_mean = np.array(cv2.mean(flatfield)[:-1])

microscope.set_lamp_voltage(VOLTAGE)
microscope.set_lamp_aperture_stop(APERTURE)

camera.set_properties(
    exposure=EXPOSURE,
    gain=GAIN,
    white_balance=WHITE_BALANCE,
    gamma=GAMMA,
)

cv2.namedWindow("Live Viewer Window", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Live Viewer Window", 1920 // 2, 1080 // 2)
curr_mag = MAG_KEYS[microscope.get_properties()["nosepiece"]]
cv2.setWindowTitle("Live Viewer Window", f"Live Viewer Window: {curr_mag}")

use_ff = False
show_guide_lines = True

while True:
    original_image = camera.get_image()
    img = original_image.copy()
    if use_ff and flatfield is not None:
        img = remove_vignette_fast(img, flatfield, flatfield_mean)

    if show_guide_lines:
        h, w, d = img.shape

        cv2.line(img, (w // 2, 0), (w // 2, h), [255, 0, 0], 2)
        cv2.line(img, (0, h // 2), (w, h // 2), [255, 0, 0], 2)

    cv2.imshow("Live Viewer Window", img)

    key = cv2.waitKey(1)
    if key == ord("q"):
        break

    # Get the current information about the image
    elif key == ord("i"):
        cam_props = camera.get_properties()
        mic_props = microscope.get_properties()
        all_props = {**cam_props, **mic_props}
        print("Properties of the camera and microscope")
        print(all_props)
        new_img = camera.get_image()

    elif key == ord("k"):
        use_ff = not use_ff

    elif key == ord("l"):
        show_guide_lines = not show_guide_lines

    elif key == ord("s"):
        cam_props = camera.get_properties()
        mic_props = microscope.get_properties()
        all_props = {**cam_props, **mic_props}
        print(all_props)

        picture_path = os.path.join(
            file_path,
            f"live_viewer_images/{VOLTAGE:.1f}_{APERTURE:.1f}_{EXPOSURE:.2f}_{GAIN:.0f}_{int(time.time())}.png",
        )
        cv2.imwrite(picture_path, original_image)

    elif key == ord("e"):
        microscope.rotate_nosepiece_forward()
        microscope.set_lamp_voltage(VOLTAGE)
        microscope.set_lamp_aperture_stop(APERTURE)
        curr_mag = MAG_KEYS[microscope.get_properties()["nosepiece"]]
        cv2.setWindowTitle("Live Viewer Window", f"Live Viewer Window: {curr_mag}")

    elif key == ord("o"):
        VOLTAGE += 0.2
        microscope.set_lamp_voltage(VOLTAGE)
        print(VOLTAGE)

    elif key == ord("d"):
        VOLTAGE -= 0.2
        microscope.set_lamp_voltage(VOLTAGE)
        print(VOLTAGE)

    elif key == ord("y"):
        APERTURE -= 0.1
        microscope.set_lamp_aperture_stop(APERTURE)
        print(APERTURE)

    elif key == ord("x"):
        APERTURE += 0.1
        microscope.set_lamp_aperture_stop(APERTURE)
        print(APERTURE)

    elif key == ord("r"):
        microscope.rotate_nosepiece_backward()
        microscope.set_lamp_voltage(VOLTAGE)
        microscope.set_lamp_aperture_stop(APERTURE)
        curr_mag = MAG_KEYS[microscope.get_properties()["nosepiece"]]
        cv2.setWindowTitle("Live Viewer Window", f"Live Viewer Window: {curr_mag}")


cv2.destroyAllWindows()

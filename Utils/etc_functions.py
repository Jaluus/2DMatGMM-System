import functools
import os
import re
import time
from typing import Generator, Type, Tuple
import json
import cv2
import numpy as np
from Drivers import (
    CameraDriverInterface,
    MicroscopeDriverInterface,
    MotorDriverInterface,
)

import Utils.conversion_functions as conversion
from GMMDetector.structures import Flake


def load_all_detection_parameters(
    material: str,
    chip_thickness: str,
    magnification: float,
) -> Tuple[dict, dict, dict, dict, np.ndarray]:
    """This function loads all the detection parameters required for a specific material, chip thickness, and magnification level.

    Args:
        material (str): The name of the material.
        chip_thickness (str): The thickness of the chip.
        magnification (float): The magnification level.

    Returns:
    Tuple[dict, dict, dict, dict, np.ndarray]: A tuple containing the following:
    - contrast_params (dict): Parameters for contrast adjustment.
    - camera_settings (dict): Settings for the camera.
    - microscope_settings (dict): Settings for the microscope.
    - magnification_params (dict): Parameters specific to the magnification level.
    - flatfield (np.ndarray): An image representing the flatfield.

    The function constructs file paths based on the input parameters and loads the corresponding JSON files and an image. It then returns these loaded parameters and the flatfield image as a tuple.
    """
    file_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parameter_directory = os.path.join(file_path, "Parameters")
    flatfield_path = os.path.join(
        parameter_directory,
        "Flatfields",
        f"{material.lower()}_{chip_thickness}_{magnification}x.png",
    )
    contrast_params_path = os.path.join(
        parameter_directory,
        "GMM_Parameters",
        f"{material.lower()}_{chip_thickness}.json",
    )
    camera_settings_path = os.path.join(
        parameter_directory,
        "Camera_Parameters",
        f"{material.lower()}_{magnification}x.json",
    )
    microscope_settings_path = os.path.join(
        parameter_directory,
        "Microscope_Parameters",
        f"{material.lower()}_{magnification}x.json",
    )
    magnification_params_path = os.path.join(
        parameter_directory,
        "Scan_Magnification",
        f"{magnification}x.json",
    )

    # Open the Jsons and get the needed Data
    with open(contrast_params_path) as f:
        contrast_params = json.load(f)
    with open(camera_settings_path) as f:
        camera_settings = json.load(f)
    with open(microscope_settings_path) as f:
        microscope_settings = json.load(f)
    with open(magnification_params_path) as f:
        magnification_params = json.load(f)

    flatfield = cv2.imread(flatfield_path)

    return (
        contrast_params,
        camera_settings,
        microscope_settings,
        magnification_params,
        flatfield,
    )


def sorted_alphanumeric(data):
    """
    sorts an array of strings alphanumericly
    """

    def convert(text):
        return int(text) if text.isdigit() else text.lower()

    def alphanum_key(key):
        return [convert(c) for c in re.split("([0-9]+)", key)]

    return sorted(data, key=alphanum_key)


def timer(func):
    """
    A simple timer decorator to time my functions
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        return_values = func(*args, **kwargs)
        print(time.time() - start)
        return return_values

    return wrapper


def set_microscope_and_camera_settings(
    microscope_settings_dict: dict,
    camera_settings_dict: dict,
    magnification_index: int,
    camera_driver: Type[CameraDriverInterface],
    microscope_driver: Type[MicroscopeDriverInterface],
):
    """Sets the Microscrope and Camera Settings as well as the right Magnification\n
    Checks if the settings have changed and updates them if they have not\n

    Args:
        microscope_settings_dict (dict): The settings for the microscope as a dict
        camera_settings_dict (dict): The settings for the camera as a dict
        magnification_idx (int): The magnification of the Microscope as the Index\n
        1: 2,5x, 2: 5x, 3: 20x, 4: 50x, 5: 100x
        camera_driver (camera_driver_class): The camera driver
        microscope_driver (microscope_driver_class): The microscope driver
    """

    # First sets the right Magnification
    microscope_driver.set_mag(magnification_index)
    time.sleep(0.5)

    # Now set the Camera Settings
    camera_driver.set_properties(**camera_settings_dict[str(magnification_index)])
    time.sleep(0.5)

    # Now set the Microscope Settings
    microscope_driver.set_lamp_voltage(
        microscope_settings_dict[str(magnification_index)]["light_voltage"]
    )
    microscope_driver.set_lamp_aperture_stop(
        microscope_settings_dict[str(magnification_index)]["aperture"]
    )
    time.sleep(0.5)

    microscope_props = microscope_driver.get_properties()
    camera_props = camera_driver.get_properties()

    print("Current Microscope Properties")
    print(microscope_props)
    print("Requested Microscope Properties")
    print(microscope_settings_dict[str(magnification_index)])
    print("")
    print("Current Camera Properties")
    print(camera_props)
    print("Requested Camera Properties")
    print(camera_settings_dict[str(magnification_index)])
    print("")


def calibrate_scope(
    motor_driver: Type[MotorDriverInterface],
    microscope_driver: Type[MicroscopeDriverInterface],
    camera_driver: Type[CameraDriverInterface],
    magnification_index: int,
    camera_settings=None,
    microscope_settings=None,
    view_field_x: float = None,
    view_field_y: float = None,
    scan_area_map: np.ndarray = None,
    use_auto_AF: bool = False,
    **kwargs,
):
    """Starts the scope calibration process

    Args:
        motor (Type[MotorDriverInterface]):
        microscope (Type[MicroscopeDriverInterface]):
        camera (Type[CameraDriverInterface]):
        needed_magnification_idx (int): The Magnificaiton which is needed to be calibrated

    Returns:
        (IMAGE , 3-Tuple ): The new Flatfield Image and the background Values, can also return None, None if none is selected
    """

    requested_magnification = conversion.magnification_index_to_magnification(
        magnification_index
    )
    new_flatfield = None

    # if a scan area map is given, drive to a location where there is a chip
    if (
        camera_settings is not None
        and microscope_settings is not None
        and scan_area_map is not None
    ):
        # extract all the coords where there is a chip and drive to the first one
        scan_area_map_eroded = cv2.erode(scan_area_map, np.ones((3, 3)), iterations=3)
        xy_coords = np.where(scan_area_map_eroded != 0)[0]

        x_pos = xy_coords[0] * view_field_x
        y_pos = xy_coords[1] * view_field_y

        print(f"moving to {x_pos} , {y_pos}")

        motor_driver.abs_move(x=x_pos, y=y_pos)

        time.sleep(5)

        set_microscope_and_camera_settings(
            microscope_settings_dict=microscope_settings,
            camera_settings_dict=camera_settings,
            magnification_index=magnification_index,
            camera_driver=camera_driver,
            microscope_driver=microscope_driver,
        )

    if (
        camera_settings is not None
        and microscope_settings is not None
        and scan_area_map is None
    ):
        # Sets the initial Camera and microscpoe Settings
        set_microscope_and_camera_settings(
            microscope_settings_dict=microscope_settings,
            camera_settings_dict=camera_settings,
            magnification_index=microscope_driver.get_properties()["nosepiece"],
            camera_driver=camera_driver,
            microscope_driver=microscope_driver,
        )

    if not use_auto_AF:
        print(
            f"""----------------------------\n
    Please calibrate the {requested_magnification} scope\n
    Use E and R to swap the scopes\n
    Use Q to finish the calibration\n
    Use F to select a new Flatfield image, if none is selected the default is used\n
    Make sure to end the calibration when in the {requested_magnification} scope\n
    ----------------------------"""
        )

        cv2.namedWindow("Calibration Window")
        current_magnification = conversion.magnification_index_to_magnification(
            microscope_driver.get_properties()["nosepiece"]
        )
        cv2.setWindowTitle(
            "Calibration Window", f"Calibration Window: {current_magnification}"
        )

        while True:
            img = camera_driver.get_image()
            # resize the image so it fits onto the screen
            img_small = cv2.resize(img, (960, 600))

            # Add a small calibration circle for the middle
            cv2.circle(
                img_small,
                (480, 300),
                10,
                color=[255, 0, 0],
                thickness=3,
            )
            cv2.imshow("Calibration Window", img_small)

            key = cv2.waitKey(1)

            # Press Q to end the calibration
            if key == ord("q"):
                # Check if the scope is actually in the right magnification
                current_nosepiece_index = microscope_driver.get_properties()[
                    "nosepiece"
                ]
                if current_nosepiece_index == magnification_index:
                    break
                else:
                    current_nosepiece_magnification = (
                        conversion.magnification_index_to_magnification(
                            current_nosepiece_index
                        )
                    )
                    print(
                        f"Please calibrate the microscope to the {requested_magnification} Scope, you are currently in the {current_nosepiece_magnification} scope"
                    )

            # Press F to set the new flatfield
            elif key == ord("f"):
                new_flatfield = img.copy()

            # Press E to reotate the Nosepiece and readjust the microscope and Camera params
            elif key == ord("e"):
                microscope_driver.rotate_nosepiece_forward()
                current_nosepiece_index = microscope_driver.get_properties()[
                    "nosepiece"
                ]
                current_magnification = conversion.magnification_index_to_magnification(
                    current_nosepiece_index
                )
                cv2.setWindowTitle(
                    "Calibration Window", f"Calibration Window: {current_magnification}"
                )
                # Set the Camera and microscope Settings
                if camera_settings is not None and microscope_settings is not None:
                    set_microscope_and_camera_settings(
                        microscope_settings_dict=microscope_settings,
                        camera_settings_dict=camera_settings,
                        magnification_index=microscope_driver.get_properties()[
                            "nosepiece"
                        ],
                        camera_driver=camera_driver,
                        microscope_driver=microscope_driver,
                    )

            # Press R to rotate the Nosepiece and readjust the microscope and Camera params
            elif key == ord("r"):
                microscope_driver.rotate_nosepiece_backward()
                current_nosepiece_index = microscope_driver.get_properties()[
                    "nosepiece"
                ]
                current_magnification = conversion.magnification_index_to_magnification(
                    current_nosepiece_index
                )
                cv2.setWindowTitle(
                    "Calibration Window", f"Calibration Window: {current_magnification}"
                )
                # Set the Camera and microscope Settings
                if camera_settings is not None and microscope_settings is not None:
                    set_microscope_and_camera_settings(
                        microscope_settings_dict=microscope_settings,
                        camera_settings_dict=camera_settings,
                        magnification_index=microscope_driver.get_properties()[
                            "nosepiece"
                        ],
                        camera_driver=camera_driver,
                        microscope_driver=microscope_driver,
                    )

        cv2.destroyAllWindows()
        return new_flatfield

    else:
        # rotate the microscope to the requested nosepiece
        set_microscope_and_camera_settings(
            microscope_settings_dict=microscope_settings,
            camera_settings_dict=camera_settings,
            magnification_index=magnification_index,
            camera_driver=camera_driver,
            microscope_driver=microscope_driver,
        )
        time.sleep(10)

        # rotate back once, when using 20x This means to 5x, and wait until it is sharp
        microscope_driver.rotate_nosepiece_backward()
        time.sleep(20)

        # rotate to 20x again
        set_microscope_and_camera_settings(
            microscope_settings_dict=microscope_settings,
            camera_settings_dict=camera_settings,
            magnification_index=magnification_index,
            camera_driver=camera_driver,
            microscope_driver=microscope_driver,
        )
        time.sleep(20)

        return None


def get_chip_directorys(scan_directory):
    """Yields all the chip directorys in the Current scan Directory

    Args:
        scan_directory (string): The path of the current scan

    Yields:
        string: A path to a chip Directory
    """
    chip_directory_names = [
        chip_directory_name
        for chip_directory_name in sorted_alphanumeric(os.listdir(scan_directory))
        if (
            os.path.isdir(os.path.join(scan_directory, chip_directory_name))
            and chip_directory_name[:4] == "Chip"
        )
    ]

    # iterate over all chip directory names
    for chip_directory_name in chip_directory_names:
        # get the full path to the chip dir
        chip_directory = os.path.join(scan_directory, chip_directory_name)

        yield chip_directory


def walk_flake_directories(scan_directory: str) -> Generator[str, None, None]:
    """Yields all the Flake directorys in the Current scan Directory

    Args:
        scan_directory (string): The apth of the current scan
        callback_function (function) : a Callback function that is beeing calld each time a new Chip is created

    Yields:
        string: An Absolute Path to a Flake Directory
    """
    chip_directory_names = [
        chip_directory_name
        for chip_directory_name in sorted_alphanumeric(os.listdir(scan_directory))
        if (
            os.path.isdir(os.path.join(scan_directory, chip_directory_name))
            and chip_directory_name[:4] == "Chip"
        )
    ]

    # iterate over all chip directory names
    for chip_directory_name in chip_directory_names:
        # get the full path to the chip dir
        chip_directory = os.path.join(scan_directory, chip_directory_name)

        # Extract all the Flake Directory names
        flake_directory_names = [
            flake_directory_name
            for flake_directory_name in sorted_alphanumeric(os.listdir(chip_directory))
            if os.path.isdir(os.path.join(chip_directory, flake_directory_name))
        ]

        # iterate over all flake directory names
        for flake_directory_name in flake_directory_names:
            # get the full path to the flake dir
            flake_directory = os.path.join(chip_directory, flake_directory_name)
            yield flake_directory


def reformat_flake_dict(
    image_dict: dict,
    flake: Flake,
    flake_directory: str,
    magnification_index: int,
) -> dict:
    """Creates a Dict used to classify the Flakes from the Image dict, as well as from the Flake_dict, corrects the flake position for the 20x scope

    Args:
        image_dict (dict): A dict containing metadata about the image
        flake (Flake): A Flake Object
        flake_directory (str): The directory where the flake is saved
        magnification_idx (int): The magnification index of the image

    Returns:
        dict, (NxMx1 Array): A dict with all the relevant keys needed to classify the Flake, A Mask of the Flake\n
        Keys are:
        "flake": {
            "chip_id": image_chip_id,
            "position_x": flake positon in mm relative to the middle of the 20x objective
            "position_y": flake positon in mm
            "size": The size of the flake in square micro meters,
            "thickness": The thickness of the flake,
            "entropy": The Shannon Entropy of the flake,
            "aspect_ratio": The aspect ratio of the flake,
            "max_sidelength": The maximum sidelength of the flake in micro meters,
            "min_sidelength": The minimum sidelength of the flake in micro meters,
            "mean_contrast_r: the red contrast of the flake,
            "mean_contrast_g": the green contrast of the flake,
            "mean_contrast_b": the blue contrast of the flake,
            "false_positive_probability": the false positive probability of the flake between 0 and 1,
            "path": The Path to the flake,
            }
        "images" : {}
    """

    MICROMETER_PER_PIXEL = conversion.MICROMETER_PER_PIXEL[magnification_index]
    IMAGE_Y_DIMENSION, IMAGE_X_DIMENSION = flake.mask.shape

    # Correcting the XY positions so the Flake is in the Middle based on the image
    flake_position_x = round(
        image_dict["motor_pos"][0]
        + (flake.center[0] - IMAGE_X_DIMENSION / 2) * MICROMETER_PER_PIXEL / 1000,
        5,
    )
    flake_position_y = round(
        image_dict["motor_pos"][1]
        + (flake.center[1] - IMAGE_Y_DIMENSION / 2) * MICROMETER_PER_PIXEL / 1000,
        5,
    )

    # Extract the Flake Path TODO: Make this more robust, doesnt support changing the path later
    # may need a database overhaul
    path = os.path.normpath(flake_directory)
    flake_path = "/".join(path.split(os.sep)[-3:])

    new_flake_dict = {
        "chip_id": image_dict["chip_id"],
        "position_x": flake_position_x,
        "position_y": flake_position_y,
        "size": conversion.pixels_to_micrometers_IDX(flake.size, magnification_index),
        "thickness": flake.thickness,
        "entropy": flake.entropy,
        "aspect_ratio": flake.aspect_ratio,
        "max_sidelength": flake.max_sidelength * MICROMETER_PER_PIXEL,
        "min_sidelength": flake.min_sidelength * MICROMETER_PER_PIXEL,
        "mean_contrast_r": flake.mean_contrast[2],
        "mean_contrast_g": flake.mean_contrast[1],
        "mean_contrast_b": flake.mean_contrast[0],
        "false_positive_probability": flake.false_positive_probability,
        "path": flake_path,
    }

    full_meta_dict = {"flake": new_flake_dict, "images": {}}

    return full_meta_dict


def fallback_convert(o):
    if isinstance(o, np.generic):
        return o.item()
    raise TypeError

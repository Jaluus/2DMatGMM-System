import json
import os
from typing import Type, List, Tuple, Generator, Optional
import time
import cv2
import numpy as np
from Drivers import (
    CameraDriverInterface,
    MicroscopeDriverInterface,
    MotorDriverInterface,
)

from GMMDetector import MaterialDetector
from GMMDetector.structures import Flake

from .etc_functions import (
    walk_flake_directories,
    set_microscope_and_camera_settings,
    reformat_flake_dict,
)
from .marker_functions import mark_on_overview, mark_flake
from .preprocessor_functions import remove_vignette_fast
import Utils.conversion_functions as conversion


def _create_folder_structure(
    scan_directory,
    magnification,
):
    magnification_path = os.path.join(scan_directory, f"{magnification}x")
    picture_path = os.path.join(magnification_path, "Pictures")
    meta_path = os.path.join(magnification_path, "Meta")

    if not os.path.exists(magnification_path):
        os.makedirs(magnification_path)

    if not os.path.exists(picture_path):
        os.makedirs(picture_path)

    if not os.path.exists(meta_path):
        os.makedirs(meta_path)

    return magnification_path, picture_path, meta_path


def raster_plate_low_magnification(
    scan_directory: str,
    motor_driver: Type[MotorDriverInterface],
    microscope_driver: Type[MicroscopeDriverInterface],
    camera_driver: Type[CameraDriverInterface],
    camera_settings: dict,
    microscope_settings: dict,
) -> Tuple[str, str]:
    """Running the algorithm to raster the plate at low magnification to get pictures of the wafers at all positions\n
    Later used to stitch the overview image

    Args:
        scan_path (str): The path to the scan directory
        motor_driver (MotorDriverInterface): The motor driver
        microscope_driver (MicroscopeDriverInterface): The microscope driver
        camera_driver (CameraDriverInterface): The camera driver
        camera_settings (dict): The settings of the camera
        microscope_settings (dict): The settings of the microscope

    Returns:
        Tuple[str, str]: The path to the image directory and the path to the metadata directory
    """

    # real x view field : 5.9048 mm
    # real y view field : 3.6905 mm
    # => 18.1 % x-overlap
    # => 10.7 % y-overlap
    # => 21 rows
    # => 31 columns

    X_STEP = 5
    Y_STEP = 3.333
    WAIT_TIME = 0.2
    MAGNIFICATION = 2.5

    ROWS = 21
    COLUMNS = 31
    NUM_IMAGES = ROWS * COLUMNS

    _, image_dir, metadata_dir = _create_folder_structure(scan_directory, MAGNIFICATION)

    # Move the motor to the start position, in this case the top left corner
    motor_driver.abs_move(0, 0)

    set_microscope_and_camera_settings(
        microscope_settings_dict=microscope_settings,
        camera_settings_dict=camera_settings,
        magnification_index=1,
        camera_driver=camera_driver,
        microscope_driver=microscope_driver,
    )

    camera_properties = camera_driver.get_properties()
    microscope_properties = microscope_driver.get_properties()

    curr_idx = 0
    start_time = time.time()
    for row_idx in range(ROWS):
        # this implements a snake-like pattern, its faster
        col = range(COLUMNS)
        if row_idx % 2 == 1:
            col = reversed(col)

        for col_idx in col:
            curr_idx += 1
            motor_driver.abs_move(row_idx * X_STEP, col_idx * Y_STEP)
            time.sleep(WAIT_TIME)

            # give a status update
            seconds_to_go = (
                (NUM_IMAGES - curr_idx) * (time.time() - start_time) / curr_idx
            )
            formatted_time = time.strftime("%H:%M:%S", time.gmtime(seconds_to_go))
            print(
                f"\r{curr_idx:4}/{NUM_IMAGES:4} scanned | Time to go : {formatted_time:15}",
                end="\r",
            )

            motor_pos = motor_driver.get_pos()
            all_props = {
                **camera_properties,
                **microscope_properties,
                "motor_pos": motor_pos,
            }

            # Save all the metadata for later reference
            json_path = os.path.join(metadata_dir, f"{curr_idx}.json")
            with open(json_path, "w") as fp:
                json.dump(all_props, fp, sort_keys=True, indent=4)

            image = camera_driver.get_image()
            image_path = os.path.join(image_dir, f"{curr_idx}.png")
            cv2.imwrite(image_path, image)

    return image_dir, metadata_dir


def image_generator(
    scan_area_map,
    motor_driver: Type[MotorDriverInterface],
    microscope_driver: Type[MicroscopeDriverInterface],
    camera_driver: Type[CameraDriverInterface],
    camera_settings: dict,
    microscope_settings: dict,
    view_field_x: float = 0.7380,
    view_field_y: float = 0.4613,
    magnification_index: int = 3,
    wait_time: float = 0.1,
) -> Generator[Tuple[Optional[np.ndarray], Optional[np.ndarray]], None, None]:
    """
    Image Generator\\
    Yields images taken from the Microscope\\
    first yields is always (None,None) as we need to move into position first
    
    Args:
        area_map (NxMx1 Array): A Map of the Chips with where to scan
        motor_driver (Type[MotorDriverInterface]): The Motordriver
        microscope_driver (ype[MicroscopeDriverInterface]): The Microscope Driver
        camera_driver (Type[CameraDriverInterface]): The Camera Driver
        microscope_settings (dict): The settings for the microscope.
        camera_settings (dict): The settings for the camera.
        view_field_x (float, optional): the x Dimension of the Picture. Defaults to 0.7380.
        view_field_y (float, optional): the y Dimension of the Picture. Defaults to 0.4613.
        magnification_index (int, optional): the used magnification index to generate time images with, default is 3.
        wait_time (float, optional): The time to wait after moving before taking a picture in seconds. Defaults to 0.2.

    Yields:
        Tuple (NxMx3 Array, Dict): The Image and the Metadata as a Dict. The First Yield will be None.\n
        Dict Keys:\n
            Image Specific:\n
                'gain' : the current gain, 0 means normal gain\n
                'exposure' : the current exposure time in seconds\n
                'gamma' : the gamma of the image, 120 means 1.2 etc..\n
                'white_balance' : the rgb white balance in tuple form e.g. (64,64,64) means 1,1,1\n
                'time' : the current time as unix timestamp\n
            Microscope Specific:\n
                'nosepiece' : positon of the nosepiece\n
                'aparture' : current ApertureStop of the EpiLamp\n
                'voltage' : current Voltage of the EpiLamp in Volts\n
            etc:\n
                'motor_pos' : The motorposition in mm (x,y)\n
                'chip_id' :  The Current Chip_id, starts at 1\n
    """

    set_microscope_and_camera_settings(
        microscope_settings_dict=microscope_settings,
        camera_settings_dict=camera_settings,
        magnification_index=magnification_index,
        camera_driver=camera_driver,
        microscope_driver=microscope_driver,
    )

    # get the camera and microscope pros as these wont change
    cam_props = camera_driver.get_properties()
    mic_props = microscope_driver.get_properties()

    num_images = cv2.countNonZero(scan_area_map)

    # Some Default Values
    curr_idx = 0
    image = None
    all_props = None
    start_time = time.time()

    for y_idx in range(scan_area_map.shape[0]):
        # this implements a snake-like pattern, its faster
        row = range(scan_area_map.shape[1])
        if y_idx % 2 == 1:
            row = reversed(row)

        for x_idx in row:
            # Dont scan anything is the areamap is 0 as only 1s are beeing scanned
            if scan_area_map[y_idx, x_idx] == 0:
                continue

            x_pos = view_field_x * x_idx
            y_pos = view_field_y * y_idx

            if x_pos < 0 or y_pos < 0:
                continue

            # move to the new Position
            motor_driver.abs_move(x_pos, y_pos)

            # Yields the Image
            yield image, all_props

            # just for Logging
            curr_idx += 1

            time_to_go = (
                (time.time() - start_time)
                / (curr_idx + 1)
                * (num_images - (curr_idx + 1))
            )
            time_string = time.strftime("%H:%M:%S", time.gmtime(time_to_go))
            print(
                f"\r{curr_idx:>5}/{num_images:<5} scanned | Time to go : ~ {time_string:15}",
                end="\r",
            )

            # Wait for move to finish
            if wait_time > 0:
                time.sleep(wait_time)

            # get the motor props
            motor_pos = motor_driver.get_pos()
            all_props = {
                **cam_props,
                **mic_props,
                "motor_pos": motor_pos,
                "chip_id": int(scan_area_map[y_idx, x_idx]),
            }

            # take the image
            image = camera_driver.get_image()

    yield image, all_props


def raster_scan_area_map(
    scan_directory: str,
    scan_area_map,
    motor_driver: Type[MotorDriverInterface],
    microscope_driver: Type[MicroscopeDriverInterface],
    camera_driver: Type[CameraDriverInterface],
    camera_settings: dict,
    microscope_settings: dict,
    view_field_x: float = 0.7380,
    view_field_y: float = 0.4613,
    magnification_index: float = 3,
    wait_time: float = 0.2,
    **kwargs,
) -> Tuple[str, str]:
    """
    Rasters the supplied scan Area Map\\
    Used to Create a Dataset as it saves all the taken Images

    Args:
        scan_directory (str): The Directory where the Scan is Located
        area_map (NxMx1 Array): A Map of the Chips with where to scan
        motor_driver (motor_driver_class): The Motordriver
        microscope_driver (microscope_driver_class): The Microscope Driver
        camera_driver (camera_driver_class): The Camera Driver
        view_field_x (float, optional): the x Dimension of the Picture. Defaults to 0.7380.
        view_field_y (float, optional): the y Dimension of the Picture. Defaults to 0.4613.
        wait_time (float, optional): The time to wait after moving before taking a picture in seconds. Defaults to 0.2.
        magnification_index (int, optional): The used magnification index. Defaults to 3.

    Returns:
        Tuple: Returns the Picture Directory and the Meta Directorey where the Image data is saved
    """

    _, image_dir, meta_dir = _create_folder_structure(
        scan_directory,
        conversion.magnification_index_to_magnification(magnification_index),
    )

    image_gen = image_generator(
        scan_area_map=scan_area_map,
        motor_driver=motor_driver,
        microscope_driver=microscope_driver,
        camera_driver=camera_driver,
        view_field_x=view_field_x,
        view_field_y=view_field_y,
        magnification_index=magnification_index,
        camera_settings=camera_settings,
        microscope_settings=microscope_settings,
        wait_time=wait_time,
    )

    for image_index, (image, prop_dict) in enumerate(image_gen):
        if image is None:
            continue

        cv2.imwrite(os.path.join(image_dir, f"{image_index}.png"), image)
        with open(os.path.join(meta_dir, f"{image_index}.json"), "w") as fp:
            json.dump(prop_dict, fp, sort_keys=True, indent=4)

    return image_dir, meta_dir


def search_scan_area_map(
    scan_directory: str,
    scan_area_map,
    motor_driver: Type[MotorDriverInterface],
    microscope_driver: Type[MicroscopeDriverInterface],
    camera_driver: Type[CameraDriverInterface],
    camera_settings: dict,
    microscope_settings: dict,
    model: MaterialDetector,
    magnification_index: int,
    view_field_x: float,
    view_field_y: float,
    flatfield=None,
    overview_image=None,
    wait_time: float = 0.2,
    **kwargs,
) -> None:
    """
    Searches the supplied scan Area Map for Flakes\\
    Used to only extract the Flakes from the Scan

    Args:
        scan_directory (str): The Directory where the Scan is Located
        area_map (NxMx1 Array): A Map of the Chips with where to scan
        motor_driver (motor_driver_class): The Motordriver
        microscope_driver (microscope_driver_class): The Microscope Driver
        camera_driver (camera_driver_class): The Camera Driver
        detector (MaterialDetector): The detector Object, initialized with values
        overview (NxMx1 Array, optional): an overview image which is beeing saved for every detected flake. Defaults to None.
        x_step (float, optional): the x Dimension of the 20x Picture. Defaults to 0.7380.
        y_step (float, optional): the y Dimension of the 20x Picture. Defaults to 0.4613.
        wait_time (float, optional): The time to wait after moving before taking a picture in seconds. Defaults to 0.2.
    """

    # Initializing the Generator, we fetch images from it
    image_gen = image_generator(
        scan_area_map=scan_area_map,
        motor_driver=motor_driver,
        microscope_driver=microscope_driver,
        camera_driver=camera_driver,
        view_field_x=view_field_x,
        view_field_y=view_field_y,
        magnification_index=magnification_index,
        camera_settings=camera_settings,
        microscope_settings=microscope_settings,
        wait_time=wait_time,
    )

    # get the flatfield mean to speed up the calculations
    if flatfield is not None:
        flatfield_mean = np.array(cv2.mean(flatfield)[:-1])

    # Autoincrementing Flake IDss
    flake_ids = {}
    original_image = None

    # 1. Scan the entire Area for flakes and save them in their respective folders
    for image, image_props in image_gen:
        # take the next image if the gotten image is invalid
        # Happends when its the first image take as we first need to move to the right position
        if image is None:
            continue

        original_image = image.copy()

        if flatfield is not None:
            image = remove_vignette_fast(
                image,
                flatfield=flatfield,
                flatfield_mean=flatfield_mean,
            )

        # run the Detection Algorithm
        detected_flakes: List[Flake] = model(image)

        # this is just ordering flakes into their repective folders
        if len(detected_flakes) != 0:
            # Create the Chip Directory for the Flake
            chip_id = image_props["chip_id"]
            chip_directory = os.path.join(scan_directory, f"Chip_{chip_id}")

            if not os.path.exists(chip_directory):
                os.makedirs(chip_directory)

            # Create a new folder for each flake
            for flake in detected_flakes:
                # increment the flake id, if it does not exist yet, create it
                flake_ids[chip_id] = flake_ids.get(chip_id, 0) + 1

                # create the flake directory
                flake_directory = os.path.join(
                    chip_directory, f"Flake_{flake_ids[chip_id]}"
                )

                os.makedirs(flake_directory)

                # mark the Flake on the overview and save it
                if overview_image is not None:
                    overview_marked = mark_on_overview(
                        overview_image,
                        image_props["motor_pos"],
                        flake_ids[chip_id],
                    )
                    overview_marked_path = os.path.join(
                        flake_directory, "overview_marked.jpg"
                    )
                    cv2.imwrite(overview_marked_path, overview_marked)

                # reformat the Flake dict to make it easier to save to the DB
                flake_meta_data = reformat_flake_dict(
                    image_props,
                    flake,
                    flake_directory,
                    magnification_index,
                )

                # Now save the Flake Metadata in the Directory
                meta_path = os.path.join(flake_directory, "meta.json")
                with open(meta_path, "w") as fp:
                    json.dump(flake_meta_data, fp, sort_keys=True, indent=4)

                # mark the flake on the image
                marked_image = mark_flake(image, flake.mask)

                # Save the original Flake Mask
                mask_path = os.path.join(flake_directory, "flake_mask.png")
                cv2.imwrite(mask_path, flake.mask)

                # save a raw copy of the image
                raw_image_path = os.path.join(flake_directory, "raw_img.png")
                cv2.imwrite(raw_image_path, original_image)

                # Save the Original eval Image
                image_path = os.path.join(flake_directory, "eval_img.jpg")
                cv2.imwrite(image_path, marked_image)


def read_meta_and_center_flakes(
    scan_directory: str,
    motor_driver: Type[MotorDriverInterface],
    microscope_driver: Type[MicroscopeDriverInterface],
    camera_driver: Type[CameraDriverInterface],
    camera_settings: dict,
    microscope_settings: dict,
    magnification_index: int = 3,
) -> None:
    # The offset in mm from the center of the 20x image as reference
    MAG_OFFSET = {
        1: (0.0406, -0.4534),
        2: (0.0406, -0.2428),
        3: (0, 0),
        4: (0.01, -0.01),
        5: (-0.03, 0.03),
    }

    MAG_WAITTIME = {
        1: 0.2,
        2: 0.2,
        3: 0.4,
        4: 1,
        5: 1,
    }

    set_microscope_and_camera_settings(
        microscope_settings_dict=microscope_settings,
        camera_settings_dict=camera_settings,
        magnification_index=magnification_index,
        camera_driver=camera_driver,
        microscope_driver=microscope_driver,
    )

    # get the properties relevant for the Image, these wont change
    cam_props = camera_driver.get_properties()
    mic_props = microscope_driver.get_properties()
    full_image_properties = {
        **cam_props,
        **mic_props,
    }

    try:
        magnification = conversion.magnification_index_to_magnification(
            magnification_index
        )
        current_image_key = f"{magnification}x"
        xy_offset = MAG_OFFSET[magnification_index]
        wait_time = MAG_WAITTIME[magnification_index]
    except KeyError as e:
        print(
            f"Wrong Magnification you need an int between 1 and 5, got {e}; defaulting to 3 (20x)"
        )
        current_image_key = "20x"
        xy_offset = MAG_OFFSET[3]
        wait_time = MAG_WAITTIME[3]

    flake_directories = walk_flake_directories(scan_directory)
    for flake_directory in flake_directories:
        image_path = os.path.join(flake_directory, f"{current_image_key}.png")
        meta_path = os.path.join(flake_directory, "meta.json")

        with open(meta_path, "r") as f:
            meta_data = json.load(f)

        flake_position_x = meta_data["flake"]["position_x"] + xy_offset[0]
        flake_position_y = meta_data["flake"]["position_y"] + xy_offset[1]

        motor_driver.abs_move(flake_position_x, flake_position_y)

        time.sleep(wait_time)

        image = camera_driver.get_image()
        cv2.imwrite(image_path, image)

        # update the meta data file
        meta_data["images"][current_image_key] = full_image_properties
        with open(meta_path, "w") as f:
            json.dump(meta_data, f, sort_keys=True, indent=4)

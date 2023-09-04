import os
import time
import json
import sys

from Drivers import CameraDriver, MicroscopeDriver, MotorDriver
import Utils.raster_functions as raster
import Utils.stitcher_functions as stitcher
import Utils.conversion_functions as conversion
import Utils.etc_functions as etc

START_TIME: float = time.time()

# Constants
SCAN_NAME: str = "SCAN_NAME"  # The Scan name for the Directory
SCAN_USER: str = "SCAN_USER"  # Your last name or Nickname
EXFOLIATED_MATERIAL: str = "MATERIAL"  # Your Material of choice
CHIP_THICKNESS: str = "THICKNESS"  # The Thickness of the Wafer
MAGNIFICATION: float = 20  # The Magnification used for the Scan
USE_AUTO_AF: bool = True  # Using the Experimental Auto Focus Calibration
COMMENT: str = ""  # The Comment for the Scan
SCAN_DIRECTORY_ROOT: str = "C:/Path/to/the/scan/directory"

META_DICT = {
    "scan_name": SCAN_NAME,
    "scan_user": SCAN_USER,
    "scan_exfoliated_material": EXFOLIATED_MATERIAL,
    "chip_thickness": CHIP_THICKNESS,
    "scan_magnificaiton": MAGNIFICATION,
    "scan_comment": COMMENT,
}

# File Paths
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
SCAN_DIRECTORY = os.path.join(SCAN_DIRECTORY_ROOT, SCAN_NAME)
scan_meta_path = os.path.join(SCAN_DIRECTORY, "meta.json")
overview_path = os.path.join(SCAN_DIRECTORY, "overview.png")
overview_compressed_path = os.path.join(SCAN_DIRECTORY, "overview_compressed.jpg")
overview_mask_path = os.path.join(SCAN_DIRECTORY, "mask.png")
scan_area_path = os.path.join(SCAN_DIRECTORY, "scan_area_map.png")

(
    contrast_params,
    camera_settings,
    microscope_settings,
    magnification_params,
    _,
) = etc.load_all_detection_parameters(
    material=EXFOLIATED_MATERIAL,
    magnification=MAGNIFICATION,
    chip_thickness=CHIP_THICKNESS,
)

# Create the Scan Directory and save the flatfield and the meta.json
if os.path.exists(SCAN_DIRECTORY):
    sys.exit("Scan Directory already exists")
else:
    os.makedirs(SCAN_DIRECTORY)
with open(scan_meta_path, "w") as fp:
    json.dump(META_DICT, fp, sort_keys=True, indent=4)

motor_driver = MotorDriver()
camera_driver = CameraDriver()
microscope_driver = MicroscopeDriver()

(
    low_magification_image_directory,
    low_magification_metadata_directory,
) = raster.raster_plate_low_magnification(
    scan_directory=SCAN_DIRECTORY,
    motor_driver=motor_driver,
    microscope_driver=microscope_driver,
    camera_driver=camera_driver,
    camera_settings=camera_settings,
    microscope_settings=microscope_settings,
)

(
    overview_image,
    scan_area_map,
) = stitcher.create_overview_image_and_map(
    image_directory=low_magification_image_directory,
    overview_path=overview_path,
    overview_mask_path=overview_mask_path,
    scan_area_path=scan_area_path,
    overview_compressed_path=overview_compressed_path,
    magnification_params=magnification_params,
)

etc.calibrate_scope(
    motor_driver=motor_driver,
    microscope_driver=microscope_driver,
    camera_driver=camera_driver,
    magnification_index=conversion.magnification_to_magnification_index(MAGNIFICATION),
    camera_settings=camera_settings,
    microscope_settings=microscope_settings,
    scan_area_map=scan_area_map,
    use_auto_AF=USE_AUTO_AF,
    **magnification_params,
)

print(f"Starting Raster Scan...")
raster.raster_scan_area_map(
    scan_directory=SCAN_DIRECTORY,
    scan_area_map=scan_area_map,
    motor_driver=motor_driver,
    microscope_driver=microscope_driver,
    camera_driver=camera_driver,
    magnification_index=conversion.magnification_to_magnification_index(MAGNIFICATION),
    camera_settings=camera_settings,
    microscope_settings=microscope_settings,
    **magnification_params,
)

formatted_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - START_TIME))
print(f"Total elapsed Time: {formatted_time}")

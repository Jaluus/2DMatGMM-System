import json
import os
import shutil
import sys
import time
import cv2

import Utils.conversion_functions as conversion
import Utils.etc_functions as etc
import Utils.raster_functions as raster
import Utils.stitcher_functions as stitcher
import Utils.upload_functions as uploader
from Drivers import CameraDriver, MicroscopeDriver, MotorDriver
from GMMDetector import MaterialDetector

START_TIME: float = time.time()

# Constants
SCAN_NAME: str = "SCAN_NAME"  # The Scan name for the Database
SCAN_USER: str = "SCAN_USER"  # Your last name or Nickname
EXFOLIATED_MATERIAL: str = "MATERIAL"  # The Material on the Wafer
CHIP_THICKNESS: str = "THICKNESS"  # The Thickness of the Wafer
MAGNIFICATION: int = 20  # Currently only 20x is supported
USED_CHANNELS: str = "BGR"  # The Channels which are used for the detection
STANDARD_DEVIATION_THRESHOLD: float = 5  # Maximum Mahalanobis Distance
SIZE_THRESHOLD: float = 200  # Flake size threshold in square micrometers (μm²)
COMMENT: str = ""  # The Comment for the Scan
USE_AUTO_AF: bool = True  # Wheter the AF should be automatically calibrated
SERVER_URL: str = "http://localhost:4999/upload"  # The URL of the Server where to send the POST Request to
SCAN_DIRECTORY_ROOT: str = "C:/Path/to/the/scan/directory/root"  # The Root Directory where the Scans should be saved

# Created Metadict
META_DICT = {
    "server_url": SERVER_URL,
    "standard_deviation_threshold": STANDARD_DEVIATION_THRESHOLD,
    "image_directory": SCAN_DIRECTORY_ROOT,
    "scan_name": SCAN_NAME,
    "scan_user": SCAN_USER,
    "scan_exfoliated_material": EXFOLIATED_MATERIAL,
    "chip_thickness": CHIP_THICKNESS,
    "scan_magnification": MAGNIFICATION,
    "chip_thickness": CHIP_THICKNESS,
    "size_threshold": SIZE_THRESHOLD,
    "scan_time": START_TIME,
    "scan_comment": COMMENT,
    "use_auto_AF": USE_AUTO_AF,
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
    flatfield,
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
cv2.imwrite(os.path.join(SCAN_DIRECTORY, "flatfield.png"), flatfield)
with open(scan_meta_path, "w") as fp:
    json.dump(META_DICT, fp, sort_keys=True, indent=4)

# Driver Initialization
motor_driver = MotorDriver()
camera_driver = CameraDriver()
microscope_driver = MicroscopeDriver()

# Detector Initialization
model = MaterialDetector(
    contrast_dict=contrast_params,
    size_threshold=conversion.micrometers_to_pixels(SIZE_THRESHOLD, MAGNIFICATION),
    standard_deviation_threshold=STANDARD_DEVIATION_THRESHOLD,
    used_channels=USED_CHANNELS,
)

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

# Remove the 2.5x images from memory as they are not needed anymore and take up a lot of space
shutil.rmtree(os.path.dirname(low_magification_image_directory))

formatted_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - START_TIME))
print(f"Time to create overview image and map: {formatted_time}")

new_flatfield = etc.calibrate_scope(
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

if new_flatfield is not None:
    flatfield = new_flatfield.copy()
    cv2.imwrite(os.path.join(SCAN_DIRECTORY, "flatfield.png"), flatfield)


scan_area_time_start = time.time()
print(f"Scanning for flakes in High Magnification...")
raster.search_scan_area_map(
    scan_directory=SCAN_DIRECTORY,
    scan_area_map=scan_area_map,
    motor_driver=motor_driver,
    microscope_driver=microscope_driver,
    camera_driver=camera_driver,
    model=model,
    flatfield=flatfield,
    magnification_index=conversion.magnification_to_magnification_index(MAGNIFICATION),
    overview_image=overview_image,
    camera_settings=camera_settings,
    microscope_settings=microscope_settings,
    **magnification_params,
)

formatted_time = time.strftime(
    "%H:%M:%S", time.gmtime(time.time() - scan_area_time_start)
)
print(f"Elapsed Time: {formatted_time}")

revisit_time_start = time.time()
print("Revisiting each Flake to take Pictures...")
for current_magnification_index in [3, 4, 5, 1, 2]:
    raster.read_meta_and_center_flakes(
        scan_directory=SCAN_DIRECTORY,
        motor_driver=motor_driver,
        microscope_driver=microscope_driver,
        camera_driver=camera_driver,
        camera_settings=camera_settings,
        microscope_settings=microscope_settings,
        magnification_index=current_magnification_index,
    )

formatted_time = time.strftime(
    "%H:%M:%S", time.gmtime(time.time() - revisit_time_start)
)
print(f"Elapsed Time during revisiting: {formatted_time}")

print("Turning off the Lamp on the Microscope to conserve the Lifetime...")
microscope_driver.lamp_off()

print("Uploading the Scan Directory...")
uploader.upload_directory(SCAN_DIRECTORY, SERVER_URL)

formatted_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - START_TIME))
print(f"Total elapsed Time: {formatted_time}")

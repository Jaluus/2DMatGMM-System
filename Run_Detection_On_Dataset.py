import json
import os
import time

import cv2
import numpy as np
from GMMDetector import MaterialDetector
from skimage.morphology import disk

from Utils.etc_functions import fallback_convert, sorted_alphanumeric
from Utils.marker_functions import mark_on_overview
from Utils.preprocessor_functions import remove_vignette_fast

SCAN_DIRECTORY: str = "/Path/to/scan/directory"  # The Directory of the scan
SCAN_NAME: str = "SCAN_NAME"  # The name of the folder
EXFOLIATED_MATERIAL: str = "MATERIAL"  # The Material on the Wafer
CHIP_THICKNESS: str = "THICKNESS"  # The Thickness of the Wafer
MAGNIFICATION: int = 20  # The used Magnification to infer flake size
USED_CHANNELS: str = "BGR"  # The Channels which are used for the detection
STANDARD_DEVIATION_THRESHOLD: float = 5  # Maximum Mahalanobis Distance
SIZE_THRESHOLD: float = 200  # Flake size threshold in square micrometers (μm²)
CONFIDENCE_THRESHOLD: float = 0.5  # Minimum confidence for a flake to be detected, it is the same as 1 - False Positive Probability

# Directory Paths
file_path = os.path.dirname(os.path.abspath(__file__))
scan_directory = os.path.join(SCAN_DIRECTORY, SCAN_NAME)

# Defining directorys
save_dir = os.path.join(scan_directory, f"{MAGNIFICATION}x", "Masked_Images")
save_dir_meta = os.path.join(scan_directory, f"{MAGNIFICATION}x", "Masked_Images_Meta")
image_dir = os.path.join(scan_directory, f"{MAGNIFICATION}x", "Pictures")
meta_dir = os.path.join(scan_directory, f"{MAGNIFICATION}x", "Meta")
overview_path = os.path.join(scan_directory, "overview.png")
marked_overview_path = os.path.join(scan_directory, "overview_marked.png")
scan_meta_data_path = os.path.join(scan_directory, "meta.json")

# Creating non Existant Paths
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
if not os.path.exists(save_dir_meta):
    os.makedirs(save_dir_meta)

# Defining parameter Paths
flatfield_path = os.path.join(
    file_path,
    "Parameters",
    "Flatfields",
    f"{EXFOLIATED_MATERIAL.lower()}_{CHIP_THICKNESS}_{MAGNIFICATION}x.png",
)
contrasts_path = os.path.join(
    file_path,
    "Parameters",
    "Contrasts",
    f"{EXFOLIATED_MATERIAL.lower()}_{CHIP_THICKNESS}.json",
)

image_names = sorted_alphanumeric(os.listdir(image_dir))
meta_names = sorted_alphanumeric(os.listdir(meta_dir))
num_images = len(image_names)

overview_image = cv2.imread(overview_path)

with open(contrasts_path) as f:
    contrast_params = json.load(f)

flatfield = cv2.imread(flatfield_path)
if flatfield is not None:
    flatfield_mean = np.array(cv2.mean(flatfield)[:-1])
else:
    raise ValueError(
        f"No flatfield found at {flatfield_path}, please supply a flatfield for the used material and magnification"
    )

start_time = time.time()
current_flake_number = 0
current_image_number = 0

model = MaterialDetector(
    contrast_dict=contrast_params,
    size_threshold=SIZE_THRESHOLD,
    standard_deviation_threshold=STANDARD_DEVIATION_THRESHOLD,
    used_channels=USED_CHANNELS,
)

for idx, (image_name, meta_name) in enumerate(zip(image_names, meta_names)):
    image_path = os.path.join(image_dir, image_name)
    detected_flake = False

    time_to_go = (time.time() - start_time) / (idx + 1) * (num_images - (idx + 1))
    time_string = time.strftime("%H:%M:%S", time.gmtime(time_to_go))
    print(
        f"{(idx+1)} / {num_images} ({(idx+1) / num_images:.0%}) | Time to go: {time_string} | Time per Image {(time.time() - start_time) / (idx+1) * 1000:.0f}ms",
        end="\r",
    )

    image = cv2.imread(image_path)
    image = remove_vignette_fast(image, flatfield, flatfield_mean=flatfield_mean)
    detected_flakes = model(image)

    for flake in detected_flakes:
        if 1 - flake.false_positive_probability < CONFIDENCE_THRESHOLD:
            continue

        detected_flake = True
        current_flake_number += 1

        outline_flake = cv2.morphologyEx(
            flake.mask,
            cv2.MORPH_GRADIENT,
            disk(1),
        )
        image[outline_flake != 0] = [0, 0, 255]

        cv2.putText(
            image,
            f"{flake.thickness}",
            flake.center,
            cv2.FONT_HERSHEY_SIMPLEX,
            thickness=1,
            fontScale=1,
            color=(0, 0, 0),
        )

        # remove the mask from the dict, since we want to save the metadata
        flake_dict = flake.to_dict()
        del flake_dict["mask"]

        with open(
            os.path.join(save_dir_meta, f"{current_flake_number}_{meta_name}"),
            "w",
        ) as f:
            json.dump(
                flake_dict,
                f,
                indent=4,
                sort_keys=True,
                default=fallback_convert,
            )

    # Run this only if a flake was found, where the FP Probability is below the threshold
    if detected_flake:
        current_image_number += 1
        print(
            f"A total of {len(detected_flakes)} flakes were found in image {image_name}"
        )

        # extract the flake position and mark it on the overview image
        meta_data = json.load(open(os.path.join(meta_dir, meta_name), "r"))
        overview_image = mark_on_overview(
            overview_image=overview_image,
            motor_pos=meta_data["motor_pos"],
        )

        cv2.imwrite(
            os.path.join(save_dir, f"{image_name}"),
            image,
        )

cv2.imwrite(marked_overview_path, overview_image)

elapsed_time = time.time() - start_time
time_string = time.strftime("%H:%M:%S", time.gmtime(time_to_go))
print(f"Total Elapsed Time: {time_string}")

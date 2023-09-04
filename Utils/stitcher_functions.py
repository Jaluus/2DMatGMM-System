"""
A collection of helper functions to stitch a collection of images together
"""
import os

import cv2
import numpy as np
from skimage import measure

from Utils.etc_functions import sorted_alphanumeric


def create_overview_image_and_map(
    image_directory: str,
    overview_path: str,
    overview_mask_path: str,
    scan_area_path: str,
    overview_compressed_path: str,
    magnification_params: dict,
):
    print("Creating Overview Image and corresponding Map...")

    print("1. Compressing 2.5x Images...", end="")
    compressed_image_directory = compress_images(image_directory)
    print("Done")

    print("2. Stitching Images...", end="")
    overview_image = stitch_image(compressed_image_directory)
    cv2.imwrite(overview_path, overview_image)
    print("Done")

    print("3. Compressing Overview Image...", end="")
    overview_image_compressed = cv2.resize(overview_image, (2000, 2000))
    cv2.imwrite(
        overview_compressed_path,
        overview_image_compressed,
        [int(cv2.IMWRITE_JPEG_QUALITY), 80],
    )
    print("Done")

    print("4. Creating mask... ", end="")
    overview_mask = create_mask_from_stitched_image(overview_image)
    cv2.imwrite(overview_mask_path, overview_mask)
    print("Done")

    print("5. Creating scan area map... ", end="")
    scan_area_map = create_scan_area_map_from_mask(
        overview_mask,
        erode_iterations=1,
        **magnification_params,
    )
    cv2.imwrite(scan_area_path, scan_area_map)
    print("Done")

    return overview_image_compressed, scan_area_map


def compress_images(
    image_directory: str,
    compressed_directory_name: str = "Compressed",
    factor: int = 4,
    quality: int = 80,
):
    """
    takes the absolut path of the picture_directory and creates a new Folder which holds all the compressed images.\n
    Images have the same name.\n
    returns the compressed image dir path
    """

    image_names = os.listdir(image_directory)
    num_pics = len(image_names)
    upper_dir = os.path.dirname(image_directory)

    compressed_directory = os.path.join(upper_dir, compressed_directory_name)
    # Create the new folder, if it does not exist
    if not os.path.exists(compressed_directory):
        os.makedirs(compressed_directory)

    # Getting the old dimensions
    img = cv2.imread(os.path.join(image_directory, image_names[0]))
    height = img.shape[1]
    width = img.shape[0]

    # The new dimensions
    new_width = int(width / factor)
    new_height = int(height / factor)

    for idx, image_name in enumerate(image_names):
        print(
            f"\rCurrent Image: {idx+1} / {num_pics}\r",
            end="",
            flush=True,
        )

        single_img_path = os.path.join(image_directory, image_name)
        img = cv2.imread(single_img_path)

        small_img = cv2.resize(img, (new_height, new_width))

        # extracte the raw image name without .png
        new_file_name = ".".join(image_name.split(".")[:-1])
        new_img_path = os.path.join(compressed_directory, f"{new_file_name}.jpg")

        # Write the image with a given quality
        cv2.imwrite(new_img_path, small_img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])

    print("")
    return compressed_directory


def stitch_image(
    picture_directory: str,
    x_rows: int = 21,
    y_rows: int = 31,
    x_pix_offset: int = 403,
    y_pix_offset: int = 273,
):
    """
    Stitches images together with the given pixel offsets and given number of rows and columns.\n
    Default Params are for 2.5x Magnificication and 5mm x-movement and 3.3333 mm y-movement\n
    Returns a stitched image and path\n
    """

    # getting all the pictures in the directory sorted!
    pic_files = sorted_alphanumeric(os.listdir(picture_directory))

    full_pic_arr_y = [None] * x_rows
    full_pic = None

    for i in range(x_rows):
        y_row = range(y_rows)

        # Compenstate the Snaking pattern during the rastering
        if i % 2 == 1:
            y_row = reversed(y_row)

        for j in y_row:
            curr_idx = i * y_rows + j
            full_path = os.path.join(picture_directory, pic_files[curr_idx])
            img = cv2.imread(full_path)

            if full_pic_arr_y[i] is None:
                full_pic_arr_y[i] = img[:y_pix_offset, :, :].copy()
            else:
                full_pic_arr_y[i] = np.concatenate(
                    (full_pic_arr_y[i], img[:y_pix_offset, :, :]),
                    axis=0,
                )

        if full_pic is None:
            full_pic = full_pic_arr_y[i][:, :x_pix_offset, :].copy()
        else:
            full_pic = np.concatenate(
                (full_pic, full_pic_arr_y[i][:, :x_pix_offset, :]),
                axis=1,
            )

    return full_pic


def create_mask_from_stitched_image(
    overview_image,
    blur_kernel: int = 5,
    blur_strength: int = 100,
):
    """
    Creates a mask form a given stitched image, using OTSUs binarization
    """

    # copy the image to make sure not to fuck up a reference
    overview_image_copy = overview_image.copy()

    overview_image_grey = cv2.cvtColor(overview_image_copy, cv2.COLOR_BGR2GRAY)
    overview_image_grey = cv2.GaussianBlur(
        overview_image_grey, (blur_kernel, blur_kernel), blur_strength
    )

    ret, mask = cv2.threshold(overview_image_grey, 127, 255, cv2.THRESH_OTSU)

    mask = cv2.erode(mask, np.ones((5, 5)), iterations=4)
    mask = cv2.dilate(mask, np.ones((5, 5)), iterations=4)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((21, 21)), iterations=5)
    return mask


def create_scan_area_map_from_mask(
    overview_mask,
    view_field_x: float = 0.7380,
    view_field_y: float = 0.4613,
    x_offset: float = 2.6121,
    y_offset: float = 1.1672,
    overview_image_y_dimension: float = 103.333,
    overview_image_x_dimension: float = 105,
    percentage_threshold: float = 0.95,
    erode_iterations: int = 0,
):
    """
    Creates a Labeled Scan Area Map and returns it

    Args:
        mask_path (str): The path to the saved black and white mask
        view_field_x (float, optional): the x View Field of the 20x in mm. Defaults to 0.7380.
        view_field_y (float, optional): the y View Field of the 20x in mm. Defaults to 0.4613.
        percentage_threshold (float,optional): The threshold for when a part of the map should still be considered as a part of the flake. Defaults to 0.9.
        overview_image_x_dimension (float, optional): The total x dimension of the overview Image in mm. Defaults to 105.
        overview_image_y_dimension (float, optional): The total y dimension of the overview Image in mm. Defaults to 103.333.
        erode_iter (int, optional): How often to erode the Mask to remove edges. Defaults to 0.

    Returns:
        labeled_scan_area (NxMx1 Array) : The scan area map
    """

    X_MOTOR_RANGE = 100
    Y_MOTOR_RANGE = 100

    # Load the mask
    # copy the image to make sure not to fuck up a reference
    mask = overview_mask.copy()

    height = mask.shape[0]
    width = mask.shape[1]

    # here we calculate the Resolution of pixels in x and y
    pixel_resolution_x = width / overview_image_x_dimension
    pixel_resolution_y = height / overview_image_y_dimension

    # Real 20x area (0.7380 x 0.4613)
    x_pixels = pixel_resolution_x * view_field_x
    y_pixels = pixel_resolution_y * view_field_y

    # Create an array which saves the points where we can raster to
    scan_area = np.zeros(
        (
            int(Y_MOTOR_RANGE / view_field_y),
            int(X_MOTOR_RANGE / view_field_x),
        )
    )
    ctr = 0
    for i in range(scan_area.shape[1]):
        for j in range(scan_area.shape[0]):
            ctr += 1
            # Crop to the part of the Image which would be seen by the 20x scope
            x_start = int(i * x_pixels + x_offset * pixel_resolution_x)
            y_start = int(j * y_pixels + y_offset * pixel_resolution_y)
            x_end = int((i + 1) * x_pixels + x_offset * pixel_resolution_x)
            y_end = int((j + 1) * y_pixels + y_offset * pixel_resolution_y)
            crop_arr = mask[y_start:y_end, x_start:x_end]

            non_zero_pixels = cv2.countNonZero(crop_arr)

            # find the percentage of non background pixels
            percentage_non_background = non_zero_pixels / (
                crop_arr.shape[0] * crop_arr.shape[1]
            )

            # Save the Image only if a certain percantage of the image is not background
            if percentage_non_background >= percentage_threshold:
                scan_area[j, i] = 1

    # Small adjustments
    scan_area = cv2.erode(scan_area, np.ones((3, 3)), iterations=1 + erode_iterations)
    scan_area = cv2.dilate(scan_area, np.ones((3, 3)), iterations=1)

    # find each chip in the image
    labeled_scan_area = measure.label(scan_area.copy())

    return labeled_scan_area.astype(np.uint8)


if __name__ == "__main__":
    pass

import cv2
import numpy as np
from numba import jit, prange


def remove_vignette_legacy(image, flatfield):
    """Removes the Vignette from the Image

    Args:
        image (NxMx3 Array): The Image with the Vignette
        flatfield (NxMx3 Array): the Flat Field in RGB

    Returns:
        (NxMx3 Array): The Image without the Vignette
    """
    # convert to hsv and cast to 16bit, to be able to add more than 255
    image_hsv = np.asarray(cv2.cvtColor(image, cv2.COLOR_BGR2HSV), dtype=np.uint16)
    flatfield_hsv = np.asarray(
        cv2.cvtColor(flatfield, cv2.COLOR_BGR2HSV), dtype=np.uint16
    )

    # get the filter and apply it to the image
    image_hsv[:, :, 2] = (
        image_hsv[:, :, 2]
        / flatfield_hsv[:, :, 2]
        * cv2.mean(flatfield_hsv[:, :, 2])[0]
    )

    # clip it back to 255
    image_hsv[:, :, 2][image_hsv[:, :, 2] > 255] = 255

    # Recast to uint8 as the color depth is 8bit per channel
    image_hsv = np.asarray(image_hsv, dtype=np.uint8)

    # reconvert to bgr
    image_no_vigentte = cv2.cvtColor(image_hsv, cv2.COLOR_HSV2BGR)
    return image_no_vigentte


@jit(nopython=True, parallel=True, fastmath=True, nogil=True)
def remove_vignette_fast(
    image,
    flatfield,
    flatfield_mean,
    max_background_value: int = 241,
):
    """Removes the Vignette from the Image

    Args:
        image (NxMx3 Array): The Image with the Vignette
        flat_field (NxMx3 Array): the Flat Field in RGB
        max_background_value (int): the maximum value of the background

    Returns:
        (NxMx3 Array): The Image without the Vignette
    """

    image_no_vigentte = np.zeros(image.shape, dtype=np.uint8)
    for i in prange(image.shape[0]):
        for j in prange(image.shape[1]):
            for k in prange(image.shape[2]):
                val = int((image[i, j, k] / flatfield[i, j, k]) * flatfield_mean[k])
                if val > max_background_value:
                    val = max_background_value
                image_no_vigentte[i, j, k] = val

    return image_no_vigentte

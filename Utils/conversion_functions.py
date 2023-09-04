MICROMETER_PER_PIXEL = {
    1: 3.0754,
    2: 1.5377,
    3: 0.3844,
    4: 0.1538,
    5: 0.0769,
}

MAGNIFICATION_TO_MAGNIFICATION_INDEX = {
    2.5: 1,
    5: 2,
    20: 3,
    50: 4,
    100: 5,
}
MAGNIFICATION_INDEX_TO_MAGNIFICATION = {
    v: k for k, v in MAGNIFICATION_TO_MAGNIFICATION_INDEX.items()
}


def magnification_index_to_magnification(magnification_index: int) -> float:
    return MAGNIFICATION_INDEX_TO_MAGNIFICATION[magnification_index]


def magnification_to_magnification_index(magnification: float) -> int:
    return MAGNIFICATION_TO_MAGNIFICATION_INDEX[magnification]


def pixels_to_micrometers_IDX(pixels: int, magnification_index: int) -> float:
    return pixels * (MICROMETER_PER_PIXEL[magnification_index] ** 2)


def micrometers_to_pixels_IDX(micrometers: float, magnification_index: int) -> int:
    return micrometers / (MICROMETER_PER_PIXEL[magnification_index] ** 2)


def pixels_to_micrometers(pixels: int, magnification: float) -> float:
    magnification_index = magnification_to_magnification_index(magnification)
    return pixels_to_micrometers_IDX(pixels, magnification_index)


def micrometers_to_pixels(micrometers: float, magnification: float) -> int:
    magnification_index = magnification_to_magnification_index(magnification)
    return micrometers_to_pixels_IDX(micrometers, magnification_index)

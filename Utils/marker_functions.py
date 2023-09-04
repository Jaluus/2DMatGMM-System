import cv2
import numpy as np


def mark_on_overview(
    overview_image,
    motor_pos,
    flake_number: int = None,
    x_motor_range: float = 105,
    y_motor_range: float = 103.333,
    x_offset: float = 2.6121,
    y_offset: float = 1.1672,
):
    overview_copy = overview_image.copy()

    picture_coords = np.array(
        [
            int((motor_pos[0] + x_offset) * overview_copy.shape[0] / x_motor_range),
            int((motor_pos[1] + y_offset) * overview_copy.shape[1] / y_motor_range),
        ]
    )

    cv2.circle(overview_copy, picture_coords, 20, [0, 255, 0], thickness=3)

    if flake_number is not None:
        cv2.putText(
            overview_copy,
            str(flake_number),
            picture_coords,
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            [0, 0, 255],
            thickness=2,
        )

    return overview_copy


def mark_flake(image, flake_mask):
    marked_image = image.copy()

    # draw the outline of the flake
    dilated_flake_mask = cv2.dilate(flake_mask, np.ones((3, 3)), iterations=2)
    flake_outline = cv2.morphologyEx(
        dilated_flake_mask,
        cv2.MORPH_GRADIENT,
        np.ones((3, 3)),
    )
    marked_image[flake_outline > 0] = (0, 0, 255)

    # draw the rotated bounding box
    dilated_flake_mask = cv2.dilate(flake_mask, np.ones((7, 7)), iterations=3)
    flake_countours, _ = cv2.findContours(
        dilated_flake_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    flake_countour = flake_countours[0]

    rotated_rect = cv2.minAreaRect(flake_countour)
    points = cv2.boxPoints(rotated_rect)
    marked_image = cv2.polylines(marked_image, [np.int0(points)], True, (0, 255, 0), 2)

    return marked_image

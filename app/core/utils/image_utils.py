import logging

import cv2
import numpy

logger = logging.getLogger(__name__)

KERNEL_3X3 = numpy.ones((3, 3), numpy.uint8)


def calculate_background_rgb(pil_image):
    """
    Calculates the background colour extremely efficiently directly from the PIL Image.
    Returns (r, g, b) or None in case of an error.
    """
    try:
        # 1. Conversion PIL -> OpenCV (NumPy)
        img_numpy = numpy.array(pil_image.convert("RGB"))
        gray = cv2.cvtColor(img_numpy, cv2.COLOR_RGB2GRAY)

        # 2. Otsu's Thresholding
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 3. Check corners
        top = mask[0, :]
        bottom = mask[-1, :]
        left = mask[1:-1, 0]
        right = mask[1:-1, -1]

        total_sum = top.sum() + bottom.sum() + left.sum() + right.sum()
        total_pixels = top.size + bottom.size + left.size + right.size

        # White text is needed for the next step (Dilation) to work properly.
        if (total_sum / total_pixels) > 127:
            mask = ~mask  # Invert the mask for white text.

        # 4. Dilation
        mask_dilated = cv2.dilate(mask, KERNEL_3X3, iterations=1)

        # 5. Masking
        mask_bg = ~mask_dilated

        if cv2.countNonZero(mask_bg) == 0:
            return None

        # DEBUG
        # debug_dir = Path(tempfile.gettempdir()) / "pdfium_debug"
        # debug_dir.mkdir(parents=True, exist_ok=True)
        # unique_id = uuid.uuid4().hex[:4]
        # cv2.imwrite(str(debug_dir / f"{unique_id}_mask_1_initial.png"), mask)
        # cv2.imwrite(str(debug_dir / f"{unique_id}_mask_2_dilated.png"), mask_dilated)
        # cv2.imwrite(str(debug_dir / f"{unique_id}_mask_3_bg.png"), mask_bg)

        # Mean (as alternative to median)
        # mean_rgb = cv2.mean(img_numpy, mask=mask_bg)
        # rgb_0 = int(mean_rgb[0])
        # rgb_1 = int(mean_rgb[1])
        # rgb_2 = int(mean_rgb[2])

        # Median
        bg_pixels = img_numpy[mask_bg == 255]
        median_rgb = numpy.median(bg_pixels, axis=0)

        rgb_0 = int(median_rgb[0])
        rgb_1 = int(median_rgb[1])
        rgb_2 = int(median_rgb[2])

        return rgb_0, rgb_1, rgb_2

    except Exception as e:
        logger.exception(f"Error calculating background RGB: {e}")
        return None

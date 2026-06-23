import logging
from ctypes import c_uint

import cv2
import numpy
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_raw

logger = logging.getLogger(__name__)

KERNEL_3X3 = numpy.ones((3, 3), numpy.uint8)


def get_char_fill_color_for_pdf_text_page(text_page: pdfium.PdfTextPage, char_index: int) -> (
        tuple[int, int, int, int] | None):
    """
    Retrieves the fill colour of a specified character in a PDF text page.
    """
    # Create empty variables with type c_uint which will be overwritten after GetFillColor call.
    r = c_uint()
    g = c_uint()
    b = c_uint()
    a = c_uint()

    if not pdfium_raw.FPDFText_GetFillColor(text_page, char_index, r, g, b, a):
        return None

    return int(r.value), int(g.value), int(b.value), int(a.value)


def pdf_charbox_to_image_bbox(
        *,
        left: float,
        bottom: float,
        right: float,
        top: float,
        page_height: float,
        scale: float,
        image_size: tuple[int, int],
        pad_x: int,
        pad_y: int,
) -> tuple[int, int, int, int] | None:
    """
    Converts character bounding box coordinates (PDF) from page-level units to image-level pixel coordinates,
    while applying padding and ensuring the resulting bounding box is valid and within the image boundaries.
    """
    x0 = max(0, int(left * scale) - pad_x)
    y0 = max(0, int((page_height - top) * scale) - pad_y)
    x1 = min(image_size[0], int(right * scale) + pad_x)
    y1 = min(image_size[1], int((page_height - bottom) * scale) + pad_y)

    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def calculate_background_rgb(pil_image) -> tuple[int, int, int] | None:
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

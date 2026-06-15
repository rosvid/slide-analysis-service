import logging
from ctypes import c_uint

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_raw
from color_contrast import AccessibilityLevel, check_contrast
from colour import Color
from django.utils.translation import gettext as _
from pptx.presentation import Presentation
from pypdfium2 import PdfDocument

from core.dtos import IssueDto, RuleResultDto
from core.enums import RuleId
from core.rules.base_rule import BaseRule
from core.utils.image_utils import calculate_background_rgb
from core.utils.pdf_utils import get_context_snippet

logger = logging.getLogger(__name__)

RENDER_DPI = 150
RENDER_SCALE = RENDER_DPI / 72
PAD_X = 3
PAD_Y = 3


class ContrastRatioRule(BaseRule):
    """
    Checks if the contrast ratio between text and background colours meets accessibility standards (WCAG 2.2).

    Possible levels are AA, AAA and AA18 for large text. See: https://www.w3.org/TR/WCAG22/ for details.
    """
    RULE_ID = RuleId.LAYOUT_CONTRAST_RATIO

    def __init__(self, level: str = "AA18"):
        self.level = level

    def apply(self, pptx: Presentation | None, pdf: PdfDocument | None) -> RuleResultDto:
        global_issues: list[IssueDto] = []
        slide_issues: dict[int, list[IssueDto]] = {}

        # DEBUG
        # debug_dir = Path(tempfile.gettempdir()) / "pdfium_debug"
        # debug_dir.mkdir(parents=True, exist_ok=True)

        if pdf:
            for page_index in range(len(pdf)):
                page_number = page_index + 1
                page_issues: list[IssueDto] = []
                logger.debug(f"Analysing Slide {page_number} for contrast ratio issues.")

                page = pdf.get_page(page_index)
                text_page = page.get_textpage()
                bitmap = None
                try:
                    bitmap = page.render(
                        scale=RENDER_SCALE,
                        rev_byteorder=True,
                        no_smoothtext=True,
                        no_smoothpath=True,
                        no_smoothimage=True,
                    )
                    page_image_pil = bitmap.to_pil()
                    page_height = page.get_height()

                    for char_index in range(text_page.count_chars()):
                        char_text = text_page.get_text_range(char_index, 1).strip()
                        if not char_text or not char_text.isalnum():
                            continue

                        char_color = _get_fill_color(text_page, char_index)
                        if char_color is None:
                            continue

                        left, bottom, right, top = text_page.get_charbox(char_index)
                        bbox = _charbox_to_image_bbox(
                            left=left,
                            bottom=bottom,
                            right=right,
                            top=top,
                            page_height=page_height,
                            scale=RENDER_SCALE,
                            image_size=page_image_pil.size,
                        )

                        if bbox is None:
                            continue

                        try:
                            char_image_pil = page_image_pil.crop(bbox)
                        except ValueError as e:
                            logger.error(f"Could not crop char '{char_text}' on Slide {page_number}: {e}")
                            continue

                        bg_color = calculate_background_rgb(char_image_pil)
                        if not bg_color:
                            continue

                        fg_color_obj = Color(rgb=tuple(channel / 255 for channel in char_color[:3]))
                        bg_color_obj = Color(rgb=(bg_color[0] / 255, bg_color[1] / 255, bg_color[2] / 255))
                        contrast_ok = check_contrast(
                            fg_color_obj,
                            bg_color_obj,
                            level=AccessibilityLevel[self.level],
                        )
                        if contrast_ok:
                            continue

                        context_snippet = get_context_snippet(text_page, char_index)

                        # DEBUG
                        # save_filename = f"slide_{page_number}_char_{char_text}_{int(bbox[0])}_pdfium.png"
                        # char_image_pil.save(debug_dir / save_filename)

                        issue = IssueDto(
                            rule_id=self.RULE_ID.value,
                            message=_("Insufficient contrast ratio for character '%(text)s' in context: '%(context_snippet)s'.") % {
                                "text": char_text,
                                "context_snippet": context_snippet,
                            },
                            details={
                                "text": char_text,
                                "context": context_snippet,
                                "foreground_color": tuple(char_color[:3]),
                                "background_color": bg_color,
                            },
                        )
                        page_issues.append(issue)

                    slide_issues[page_number] = page_issues
                finally:
                    if bitmap is not None:
                        bitmap.close()
                    text_page.close()
                    page.close()

        return RuleResultDto(global_issues=global_issues, slide_issues=slide_issues)


def _get_fill_color(text_page: pdfium.PdfTextPage, char_index: int) -> tuple[int, int, int, int] | None:
    # Create empty variables with type c_uint which will be overwritten after GetFillColor call.
    r = c_uint()
    g = c_uint()
    b = c_uint()
    a = c_uint()

    if not pdfium_raw.FPDFText_GetFillColor(text_page, char_index, r, g, b, a):
        return None

    return int(r.value), int(g.value), int(b.value), int(a.value)


def _charbox_to_image_bbox(
        *,
        left: float,
        bottom: float,
        right: float,
        top: float,
        page_height: float,
        scale: float,
        image_size: tuple[int, int],
) -> tuple[int, int, int, int] | None:
    x0 = max(0, int(left * scale) - PAD_X)
    y0 = max(0, int((page_height - top) * scale) - PAD_Y)
    x1 = min(image_size[0], int(right * scale) + PAD_X)
    y1 = min(image_size[1], int((page_height - bottom) * scale) + PAD_Y)

    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1

import pypdfium2.raw as pdfium_raw
from django.utils.translation import gettext as _
from pptx.presentation import Presentation
from pypdfium2 import PdfDocument

from core.dtos import IssueDto, RuleResultDto
from core.enums import RuleId
from core.rules.base_rule import BaseRule
from core.utils.pdf_utils import get_context_snippet


class MinFontSizeRule(BaseRule):
    """
    Rule to ensure that the minimum rendered font size on a slide is not less than the configured threshold.
    Finds the character with the smallest font size and reports it as an issue.
    """
    RULE_ID = RuleId.TEXT_MIN_FONT_SIZE

    def __init__(self, min_font_size: int = 24):
        self.min_font_size = min_font_size

    def apply(self, pptx: Presentation | None, pdf: PdfDocument | None) -> RuleResultDto:
        global_issues: list[IssueDto] = []
        slide_issues: dict[int, list[IssueDto]] = {}

        if pdf:
            for page_index in range(len(pdf)):
                page_number = page_index + 1
                page = pdf.get_page(page_index)
                text_page = page.get_textpage()
                try:
                    min_found_size: int | None = None
                    min_found_char: str | None = None
                    min_found_index: int | None = None

                    for char_index in range(text_page.count_chars()):
                        char_text = text_page.get_text_range(char_index, 1)
                        if not char_text or not char_text.isalnum():
                            continue

                        char_size_rounded = round(pdfium_raw.FPDFText_GetFontSize(text_page, char_index))
                        if char_size_rounded >= self.min_font_size:
                            continue

                        if min_found_size is None or char_size_rounded < min_found_size:
                            min_found_size = char_size_rounded
                            min_found_char = char_text
                            min_found_index = char_index

                    if min_found_size is not None and min_found_index is not None:
                        context_snippet = get_context_snippet(text_page, min_found_index)
                        issue = IssueDto(
                            rule_id=self.RULE_ID.value,
                            message=_("Slide uses character '%(text)s' with size %(font_size)d, which is less than the recommended size of %(min)d in context: '%(context_snippet)s'.") % {
                                "text": min_found_char or "?",
                                "font_size": min_found_size,
                                "min": self.min_font_size,
                                "context_snippet": context_snippet,
                            },
                            details={
                                "text": min_found_char,
                                "context": context_snippet,
                                "font_size": min_found_size,
                                "min_font_size": self.min_font_size,
                            },
                        )
                        slide_issues[page_number] = [issue]
                finally:
                    text_page.close()
                    page.close()

        return RuleResultDto(
            global_issues=global_issues,
            slide_issues=slide_issues,
        )

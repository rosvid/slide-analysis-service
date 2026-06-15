from django.utils.translation import gettext as _
from pptx.presentation import Presentation
from pypdfium2 import PdfDocument

from core.dtos import IssueDto, RuleResultDto
from core.enums import RuleId
from core.rules.base_rule import BaseRule
from core.utils.pdf_utils import extract_lines_from_text_page


class MaxWordsPerRowRule(BaseRule):
    """
    Checks if the number of words in any text row exceeds a given maximum.
    """
    RULE_ID = RuleId.TEXT_MAX_WORDS_PER_ROW

    def __init__(self, max_words: int = 6):
        self.max_words = max_words

    def apply(self, pptx: Presentation | None, pdf: PdfDocument | None) -> RuleResultDto:
        global_issues: list[IssueDto] = []
        slide_issues: dict[int, list[IssueDto]] = {}

        if pdf:
            for page_index in range(len(pdf)):
                page_number = page_index + 1
                page = pdf.get_page(page_index)
                text_page = page.get_textpage()
                try:
                    page_issues: list[IssueDto] = []

                    for line in extract_lines_from_text_page(text_page):
                        words = [word for word in line.split() if any(char.isalnum() for char in word)]
                        if len(words) <= self.max_words:
                            continue

                        issue = IssueDto(
                            rule_id=self.RULE_ID.value,
                            message=_("Row contains %(count)d words, which exceeds the recommended maximum of %(max)d.") % {
                                "count": len(words),
                                "max": self.max_words,
                            },
                            details={
                                "word_count": len(words),
                                "max_words": self.max_words,
                                "row_text": line,
                            },
                        )
                        page_issues.append(issue)

                    slide_issues[page_number] = page_issues
                finally:
                    text_page.close()
                    page.close()

        return RuleResultDto(
            global_issues=global_issues,
            slide_issues=slide_issues,
        )

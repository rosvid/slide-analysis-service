import logging
from pathlib import Path

from django.utils.translation import gettext as _
from pptx.presentation import Presentation
from pypdfium2 import PdfDocument

from core.dtos import IssueDto, RuleResultDto
from core.enums import RuleId
from core.rules.base_rule import BaseRule
from core.utils.fonts_utils import get_used_base_fonts_in_pptx

logger = logging.getLogger(__name__)


class MaxFontsRule(BaseRule):
    """
    Rule to ensure that the maximum number of different fonts used in a presentation is not more than 3.
    """
    RULE_ID = RuleId.TEXT_MAX_FONTS

    def __init__(self, max_fonts: int = 3):
        self.max_fonts = max_fonts

    def apply(self, pptx: Presentation | None, pdf: PdfDocument | None) -> RuleResultDto:
        global_issues: list[IssueDto] = []
        slide_issues: dict[int, list[IssueDto]] = {}

        if pptx:
            fonts_used = get_used_base_fonts_in_pptx(pptx)

            if len(fonts_used) > self.max_fonts:
                issue = IssueDto(
                    rule_id=self.RULE_ID.value,
                    message=_("Presentation uses %(count)d different fonts, which exceeds the maximum allowed of %(max)d.") % {
                        "count": len(fonts_used),
                        "max": self.max_fonts
                    },
                    details={
                        "fonts_used": list(fonts_used),
                        "max_fonts": self.max_fonts
                    }
                )
                global_issues = [issue]

        return RuleResultDto(
            global_issues=global_issues,
            slide_issues=slide_issues
        )

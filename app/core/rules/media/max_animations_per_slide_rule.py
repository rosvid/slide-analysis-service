from django.utils.translation import gettext as _
from pypdfium2 import PdfDocument
from pptx.presentation import Presentation

from core.dtos import IssueDto, RuleResultDto
from core.enums import RuleId
from core.rules.base_rule import BaseRule


class MaxAnimationsPerSlideRule(BaseRule):
    """
    Checks if the number of animations on any slide exceeds a given maximum.
    """
    RULE_ID = RuleId.MEDIA_MAX_ANIMATIONS_PER_SLIDE

    def __init__(self, max_animations: int = 0):
        self.max_animations = max_animations

    def apply(self, pptx: Presentation | None, pdf: PdfDocument | None) -> RuleResultDto:
        global_issues: list[IssueDto] = []
        slide_issues: dict[int, list[IssueDto]] = {}

        # Look for timing nodes in the slide, layout and master that have a presetClass attribute, which indicates an animation effect.
        # Ignore 'mediacall' because it is used for media elements and does not necessarily indicate an animation effect.
        xpath_query = ".//p:tnLst//p:cTn[@presetClass and @presetClass!='mediacall' and (@nodeType='clickEffect' or @nodeType='afterEffect')]"

        if pptx:
            for i, slide in enumerate(pptx.slides, start=1):
                master_anim_count = len(slide.slide_layout.slide_master.element.xpath(xpath_query))
                layout_anim_count = len(slide.slide_layout.element.xpath(xpath_query))
                animation_count = len(slide.element.xpath(xpath_query))
                animation_count += layout_anim_count + master_anim_count

                if animation_count > self.max_animations:
                    issue = IssueDto(
                        rule_id=self.RULE_ID.value,
                        message=_("Slide contains %(animation_count)d animations, which exceeds the recommended maximum of %(max)d.") % {
                            "animation_count": animation_count,
                            "max": self.max_animations
                        },
                        details={
                            "animation_count": animation_count,
                            "max_animations": self.max_animations
                        }
                    )
                    slide_issues[i] = [issue]

        return RuleResultDto(
            global_issues=global_issues,
            slide_issues=slide_issues
        )

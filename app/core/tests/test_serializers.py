import json
import logging

from django.test import SimpleTestCase

from core.dtos import (
    AnalysisResultDto,
    FileInfoDto,
    SummaryDto,
    IssueDto,
    SlideResultDto,
)
from core.serializers import AnalysisResultDtoSerializer

logger = logging.getLogger(__name__)


class SerializersTest(SimpleTestCase):
    def test_analysis_result_dto_serialization(self):
        # 1. Create DTOs with example data.
        file_info_dto = FileInfoDto(
            file_name="Presentation.pptx",
            file_size=123456,
            total_slides=5
        )

        summary_dto = SummaryDto(
            total_issues_found=5,
            slides_with_issues=3,
            rules_checked=[
                "TEXT_MAX_FONTS",
                "TEXT_MAX_WORDS_PER_ROW",
                "TEXT_MAX_WORDS_PER_SLIDE",
                "TEXT_MAX_BULLET_POINTS_PER_SLIDE",
                "MEDIA_MIN_IMAGE_PPI",
            ]
        )

        global_issues_dto = [
            IssueDto(
                rule_id="TEXT_MAX_FONTS",
                message="Presentation uses 3 different fonts, which exceeds the maximum allowed of 2.",
                details={"fonts_used": ["Arial", "Calibri", "Times New Roman"], "limit": 2}
            )
        ]

        slide_results_dto = [
            SlideResultDto(slide_number=1, has_issues=False, issues=[]),
            SlideResultDto(
                slide_number=2,
                has_issues=True,
                issues=[
                    IssueDto(
                        rule_id="TEXT_MAX_WORDS_PER_SLIDE",
                        message="Slide contains 58 words, which exceeds the recommended maximum of 40.",
                        details={"word_count": 58, "limit": 40}
                    )
                ]
            ),
            SlideResultDto(
                slide_number=3,
                has_issues=True,
                issues=[
                    IssueDto(
                        rule_id="MEDIA_MIN_IMAGE_PPI",
                        message="Image image_1.png has an effective resolution of 96 PPI, which is below the recommended minimum of 150 PPI.",
                        details={"image_name": "image_1.png", "ppi": 96, "limit": 150}
                    ),
                    IssueDto(
                        rule_id="TEXT_MAX_WORDS_PER_ROW",
                        message="Row contains 11 words, which exceeds the recommended maximum of 6.",
                        details={
                            "line_text": "Unsere neue, revolutionäre und marktführende Produktstrategie für das kommende Geschäftsjahr.",
                            "word_count": 11,
                            "limit": 6
                        }
                    )
                ]
            ),
            SlideResultDto(
                slide_number=4,
                has_issues=True,
                issues=[
                    IssueDto(
                        rule_id="TEXT_MAX_BULLET_POINTS_PER_SLIDE",
                        message="Slide contains 7 bullet points, which exceeds the recommended maximum of 6.",
                        details={"bullet_point_count": 7, "limit": 6}
                    ),
                    IssueDto(
                        rule_id="TEXT_MAX_WORDS_PER_SLIDE",
                        message="Slide contains45 words, which exceeds the recommended maximum of 40.",
                        details={"word_count": 45, "limit": 40}
                    )
                ]
            ),
            SlideResultDto(slide_number=5, has_issues=False, issues=[])
        ]

        analysis_result_dto = AnalysisResultDto(
            analysis_id="a1b2c3d4-e5f6-7890-1234-567890abcdef",
            analysis_timestamp="2023-10-27T14:30:00Z",
            file_info=file_info_dto,
            summary=summary_dto,
            global_issues=global_issues_dto,
            slide_results=slide_results_dto
        )

        # 2. Serialise DTO.
        serializer = AnalysisResultDtoSerializer(instance=analysis_result_dto)
        serialised_data = serializer.data

        # 3. Pretty print.
        logger.info(json.dumps(serialised_data, indent=4, ensure_ascii=False))

        # 4. Check, if correctly serialised.
        self.assertEqual(serialised_data["analysis_id"], "a1b2c3d4-e5f6-7890-1234-567890abcdef")
        self.assertEqual(len(serialised_data["slide_results"]), 5)
        self.assertEqual(serialised_data["summary"]["total_issues_found"], 5)

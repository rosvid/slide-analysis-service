import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import pypdfium2 as pdfium
from django.conf import settings

from core.analysers.base_analyser import BaseAnalyser
from core.dtos import AnalysisResultDto, FileInfoDto, SummaryDto, SlideResultDto, IssueDto
from core.enums import RuleId
from core.rules.base_rule import BaseRule

logger = logging.getLogger(__name__)


# This is a very basic implementation for PDF analysis, mainly to demonstrate the structure and flow.
class PdfAnalyser(BaseAnalyser):
    def analyse(self, presentation_file, file_extension: str, rules: list[BaseRule]) -> AnalysisResultDto:
        with NamedTemporaryFile(delete=False, suffix=file_extension, dir=settings.TMP_DIR) as tmp:
            tmp.write(presentation_file.read_bytes())
            tmp_path = Path(tmp.name)
            logger.debug(f"Saved uploaded PDF file to temporary path: {tmp_path}")

        try:
            with pdfium.PdfDocument(tmp_path) as pdf:
                global_issues_collection: dict[RuleId, list[IssueDto]] = {}
                slide_issues_collection: dict[RuleId, dict[int, list[IssueDto]]] = {}  # PDF pages act as slides.

                for rule in rules:
                    result = rule.apply(None, pdf)
                    global_issues_collection[rule.rule_id] = result.global_issues
                    slide_issues_collection[rule.rule_id] = result.slide_issues

                file_info_dto = FileInfoDto(
                    file_name=os.path.basename(presentation_file.name),
                    file_size=os.path.getsize(tmp_path),
                    total_slides=len(pdf.pages),
                )

                total_slides_issues = sum(sum(len(issues) for issues in slide_issues.values()) for slide_issues in
                                          slide_issues_collection.values())
                total_sum_issues = sum(
                    len(issues) for issues in global_issues_collection.values()) + total_slides_issues
                slides_with_issues = len({slide_number for issues in slide_issues_collection.values() for slide_number
                                          in issues if issues[slide_number]}
                                         )

                summary_dto = SummaryDto(
                    total_issues_found=total_sum_issues,
                    slides_with_issues=slides_with_issues,
                    rules_checked=[rule.rule_id.value for rule in rules],
                )

                global_issues_dtos: list[IssueDto] = []
                for rule_id, issues in global_issues_collection.items():
                    for issue in issues:
                        issue.rule_id = rule_id.value
                        global_issues_dtos.append(issue)

                slide_results_dtos: list[SlideResultDto] = []
                for slide_number in range(1, len(pdf.pages) + 1):
                    slide_issues = []
                    for rule_id, issues in slide_issues_collection.items():
                        if slide_number in issues:
                            slide_issues.extend(issues[slide_number])

                    has_issues = len(slide_issues) > 0
                    slide_result_dto = SlideResultDto(
                        slide_number=slide_number,
                        has_issues=has_issues,
                        issues=slide_issues,
                    )
                    slide_results_dtos.append(slide_result_dto)

                analysis_result_dto = AnalysisResultDto(
                    analysis_id=str(uuid.uuid4()),
                    analysis_timestamp=datetime.now().isoformat(),
                    file_info=file_info_dto,
                    summary=summary_dto,
                    global_issues=global_issues_dtos,
                    slide_results=slide_results_dtos,
                )

                return analysis_result_dto
        finally:
            if tmp_path.exists():
                os.remove(tmp_path)

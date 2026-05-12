"""
Data Transfer Objects (DTOs) for Slide analysis results.
"""
from dataclasses import dataclass


@dataclass
class FileInfoDto:
    file_name: str
    file_size: str
    total_slides: int


@dataclass
class SummaryDto:
    total_issues_found: int
    slides_with_issues: int
    rules_checked: list[str]


@dataclass
class IssueDto:
    rule_id: str
    message: str
    details: dict


@dataclass
class SlideResultDto:
    slide_number: int
    has_issues: bool
    issues: list[IssueDto]


@dataclass
class AnalysisResultDto:
    analysis_id: str
    analysis_timestamp: str
    file_info: FileInfoDto
    summary: SummaryDto
    global_issues: list[IssueDto]
    slide_results: list[SlideResultDto]


@dataclass
class RuleResultDto:
    global_issues: list[IssueDto]
    slide_issues: dict[int, list[IssueDto]]

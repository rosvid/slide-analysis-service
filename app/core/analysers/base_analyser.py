from abc import ABC, abstractmethod

from core.dtos import AnalysisResultDto
from core.rules.base_rule import BaseRule


class BaseAnalyser(ABC):
    @abstractmethod
    def analyse(self, presentation_file, file_extension: str, rules: list[BaseRule]) -> AnalysisResultDto:
        """
        Analyses a file based on specified rules and generates a detailed analysis report.
        Each format (e.g., PPT, PPTX, PDF) has its own implementation.
        """
        pass

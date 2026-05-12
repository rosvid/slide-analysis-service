import json
import logging
import statistics
from time import perf_counter

from django.conf import settings
from django.test import SimpleTestCase

from core.enums import RuleId
from core.serializers import AnalysisResultDtoSerializer
from core.services import AnalyserService
from core.utils.main_utils import get_latest_powerpoint, get_latest_pdf, get_ppt_files_from_directory

logger = logging.getLogger(__name__)


class ServicesTest(SimpleTestCase):
    def test_analyser_service_for_pptx(self):
        pptx_file = get_latest_powerpoint(settings.TEST_PPTX_DIR)
        self.assertIsNotNone(pptx_file, f"No PowerPoint file found in {settings.TEST_PPTX_DIR} to test with.")

        rules_config = []
        analyser_service = AnalyserService()

        with open(pptx_file, "rb") as ppt_file:
            analysis_result_dto = analyser_service.analyse(ppt_file, rules_config)

        serializer = AnalysisResultDtoSerializer(instance=analysis_result_dto)
        serialized_data = serializer.data
        self.assertTrue(len(serialized_data) > 0, "Serialized data should not be empty.")
        self.assertIn("analysis_id", serialized_data)
        logger.info(json.dumps(serialized_data, indent=4))

    def test_analyser_service_for_pdf(self):
        pdf_file = get_latest_pdf(settings.TEST_PPTX_DIR)
        self.assertIsNotNone(pdf_file, f"No PDF file found in {settings.TEST_PPTX_DIR} to test with.")

        analyser_service = AnalyserService()
        analysis_result_dto = analyser_service.analyse(pdf_file)

        serializer = AnalysisResultDtoSerializer(instance=analysis_result_dto)
        serialized_data = serializer.data
        self.assertTrue(len(serialized_data) > 0, "Serialized data should not be empty.")
        self.assertIn("analysis_id", serialized_data)
        logger.info(json.dumps(serialized_data, indent=4))

    def test_analyser_for_directory(self):
        rules_config = [RuleId.TEXT_MAX_WORDS_PER_ROW.value]
        analyser_service = AnalyserService()
        analysis_results = []
        for ppt_file in get_ppt_files_from_directory(settings.TEST_PPTX_DIR):
            analysis_result_dto = analyser_service.analyse(ppt_file, rules_config)
            serializer = AnalysisResultDtoSerializer(instance=analysis_result_dto)
            serialized_data = serializer.data
            analysis_results.append(serialized_data)
        self.assertTrue(len(analysis_results) > 0, "Analysis results should not be empty.")
        logger.info(json.dumps(analysis_results, indent=4))

    def test_analyser_performance_benchmark(self):
        analyser_service = AnalyserService()
        rules_config = [RuleId.LAYOUT_CONTRAST_RATIO.value]

        ppt_files = list(get_ppt_files_from_directory(settings.TEST_PPTX_DIR))
        self.assertTrue(len(ppt_files) > 0, "No PPTX files found for testing.")

        NUM_RUNS = 10
        execution_times = []

        logger.info(f"--- Start benchmark: {NUM_RUNS} runs ---")

        analysis_results = []
        for run in range(1, NUM_RUNS + 1):
            start_time = perf_counter()

            for ppt_file in ppt_files:
                analysis_result_dto = analyser_service.analyse(ppt_file, rules_config)
                serializer = AnalysisResultDtoSerializer(instance=analysis_result_dto)
                analysis_results.append(serializer.data)

            end_time = perf_counter()
            duration = end_time - start_time
            execution_times.append(duration)

            logger.info(f"Run {run}/{NUM_RUNS} finished in {duration:.3f} seconds.")

        avg_time = statistics.mean(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)

        logger.info("=" * 50)
        logger.info(" BENCHMARK results")
        logger.info("=" * 50)
        logger.info(f" Number of files: {len(ppt_files)}")
        logger.info(f" Runs:     {NUM_RUNS}")
        logger.info(f" Average:   {avg_time:.3f} seconds.")
        logger.info(f" Fastest:    {min_time:.3f} seconds.")
        logger.info(f" Slowest:    {max_time:.3f} seconds.")
        logger.info("=" * 50)

        self.assertTrue(len(analysis_results) > 0, "Analysis results should not be empty.")

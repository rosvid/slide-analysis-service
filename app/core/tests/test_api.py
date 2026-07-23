import json
import logging
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient

from core.utils.main_utils import get_ppt_files_from_directory

logger = logging.getLogger(__name__)


@override_settings(TEST_PPTX_DIR=Path(settings.TEST_PPTX_DIR) / "Evaluation/Extended")
class ApiTest(SimpleTestCase):
    def test_analyse_all_evaluation_files(self):
        pptx_files = get_ppt_files_from_directory(settings.TEST_PPTX_DIR)

        self.assertTrue(len(pptx_files) > 0, f"No PPTX files found in {settings.TEST_PPTX_DIR}")
        logger.info(f"Found {len(pptx_files)} files to analyse in {settings.TEST_PPTX_DIR}")

        total_start = perf_counter()
        timings: list[tuple[str, float]] = []

        for pptx_file in pptx_files:
            file_start = perf_counter()

            with open(pptx_file, "rb") as file:
                response = APIClient().post(
                    "/analyse/",
                    {"file": file},
                    format="multipart",
                    HTTP_X_API_KEY=settings.SECRET_API_KEY,
                    HTTP_ACCEPT_LANGUAGE="en",
                )

            file_duration = perf_counter() - file_start
            timings.append((pptx_file.name, file_duration))

            self.assertEqual(response.status_code, 200, f"Analysis failed for {pptx_file.name}.")

            result_path = pptx_file.with_suffix(".json")
            result_path.write_text(
                json.dumps(response.json(), indent=4, ensure_ascii=False),
                encoding="utf-8",
            )

        total_duration = perf_counter() - total_start

        for filename, duration in timings:
            logger.info(f"{filename} processed in {duration:.3f}s")
        logger.info(f"Total: {len(timings)} files processed in {total_duration:.3f}s "
                    f"(avg {total_duration / len(timings):.3f}s per file)")

import logging
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase
from pptx import Presentation

from core.utils.fonts_utils import get_used_base_fonts_in_pptx
from core.utils.main_utils import get_latest_powerpoint, convert_pptx_to_pdf, get_ppt_files_from_directory

logger = logging.getLogger(__name__)


class UtilsTest(SimpleTestCase):
    def test_convert_pptx_to_pdf(self):
        pptx_file = get_latest_powerpoint(settings.TEST_PPTX_DIR)
        self.assertIsNotNone(pptx_file, f"No PowerPoint file found in {settings.TEST_PPTX_DIR} to test with.")

        pdf_path = convert_pptx_to_pdf(pptx_file, Path(settings.TMP_DIR))
        self.assertTrue(pdf_path.exists(), "Converted PDF file should exist.")
        self.assertTrue(pdf_path.suffix.lower() == ".pdf", "Converted file should have a .pdf extension.")

    def test_get_used_fonts(self):
        pptx_file = get_ppt_files_from_directory(settings.TEST_PPTX_DIR)[0]
        self.assertIsNotNone(pptx_file, f"No PowerPoint file found in {settings.TEST_PPTX_DIR} for testing.")

        presentation = Presentation(pptx_file)
        used_fonts = get_used_base_fonts_in_pptx(presentation)
        self.assertIsInstance(used_fonts, set)
        logger.info(f"Used fonts: {used_fonts}")

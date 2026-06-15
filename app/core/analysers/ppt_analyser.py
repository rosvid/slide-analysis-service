import logging
import os
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from django.conf import settings

from core.analysers.base_analyser import BaseAnalyser
from core.analysers.pptx_analyser import PptxAnalyser
from core.dtos import AnalysisResultDto
from core.rules.base_rule import BaseRule
from core.utils.main_utils import convert_ppt_to_pptx

logger = logging.getLogger(__name__)


class PptAnalyser(BaseAnalyser):
    def __init__(self):
        self.pptx_analyser = PptxAnalyser()

    def analyse(self, presentation_file, file_extension: str, rules: list[BaseRule]) -> AnalysisResultDto:
        file_name = Path(presentation_file.name).stem
        unique_id = uuid.uuid4().hex[:4]
        subfolder_name = f"{file_name[:10]}_{unique_id}"

        run_tmp_dir = Path(settings.TMP_DIR) / subfolder_name
        run_tmp_dir.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(delete=False, suffix=file_extension, dir=run_tmp_dir) as tmp:
            if isinstance(presentation_file, Path):
                tmp.write(presentation_file.read_bytes())
            else:
                tmp.write(presentation_file.read())
            tmp_path = Path(tmp.name)
            logger.debug(f"Saved uploaded PPT file to temporary path: {tmp_path}")

        pptx_file = None
        try:
            pptx_path = convert_ppt_to_pptx(tmp_path, run_tmp_dir)
            pptx_file = Path(pptx_path)

            # Delegate to PptxAnalyser for the actual analysis.
            return self.pptx_analyser.analyse(pptx_file, ".pptx", rules)

        finally:
            if settings.DEBUG:
                logger.debug(f"DEBUG mode is on. Not removing temporary files: {tmp_path} and {pptx_file}.")
            else:
                if tmp_path.exists():
                    os.remove(tmp_path)
                if pptx_file and pptx_file.exists():
                    os.remove(pptx_file)

import logging
import subprocess
from pathlib import Path
from typing import Optional

from django.conf import settings
from unoserver.client import UnoClient

logger = logging.getLogger(__name__)


def get_latest_powerpoint(directory: str) -> Optional[Path]:
    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        raise ValueError(f"Directory {directory} does not exist or is not a directory.")

    # Get all PowerPoint files in the directory.
    powerpoint_files = list(directory_path.glob("*.ppt")) + list(directory_path.glob("*.pptx"))
    if not powerpoint_files:
        latest_file = None
    else:
        # Find the latest PPTX file.
        latest_file = max(powerpoint_files, key=lambda x: x.stat().st_mtime)

    return latest_file


def get_latest_pdf(directory: str) -> Optional[Path]:
    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        raise ValueError(f"Directory {directory} does not exist or is not a directory.")

    # Get all PDF files in the directory.
    pdf_files = list(directory_path.glob("*.pdf"))
    if not pdf_files:
        latest_file = None
    else:
        # Find the latest PDF file.
        latest_file = max(pdf_files, key=lambda x: x.stat().st_mtime)

    return latest_file


def get_ppt_files_from_directory(directory: str) -> list[Path]:
    """
    Returns a list of all PowerPoint files in the specified directory.
    """
    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        raise ValueError(f"Directory {directory} does not exist or is not a directory.")

    # Get all PowerPoint files in the directory
    ppt_files = list(directory_path.glob("*.ppt")) + list(directory_path.glob("*.pptx"))
    logger.info(f"Found {len(ppt_files)} PowerPoint files in {directory}.")
    return ppt_files


def convert_pptx_to_pdf(pptx_path: Path, output_dir: Path) -> Path:
    """
    Converts a PowerPoint file to PDF using UnoServer via UnoClient.
    """
    uno_host = settings.UNOSERVER_HOST
    uno_port = settings.UNOSERVER_PORT

    if not pptx_path.exists():
        raise FileNotFoundError(f"Input file not found: {pptx_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{pptx_path.stem}.pdf"

    try:
        client = UnoClient(uno_host, uno_port)

        with open(pptx_path, "rb") as f:
            file_data = f.read()

        pdf_bytes = client.convert(
            convert_to="pdf",
            indata=file_data,
        )

        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        logger.debug(f"Successfully converted {pptx_path} to {pdf_path} using UnoServer at {uno_host}:{uno_port}")

    except Exception as e:
        raise RuntimeError(f"UnoServer error ({uno_host}:{uno_port}): {e}") from e

    return pdf_path


def convert_pptx_to_pdf_with_local_libreoffice(pptx_path: Path) -> Path:
    """
    Converts a PowerPoint file to PDF using LibreOffice in headless mode.

    For internal use without docker.
    """
    # Your libreoffice installation path should be set here.
    libreoffice_path = r"C:\Program Files\LibreOffice\program\soffice.exe"
    output_dir = Path(settings.TMP_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            [
                libreoffice_path,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_dir),
                str(pptx_path)
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        pdf_path = output_dir / f"{pptx_path.stem}.pdf"
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF conversion failed. File not found. LibreOffice stdout: {result.stdout}")
        return pdf_path
    except FileNotFoundError:
        raise RuntimeError(f"LibreOffice executable not found at {libreoffice_path}. Please check the path.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error during conversion with LibreOffice: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred during conversion: {e}")

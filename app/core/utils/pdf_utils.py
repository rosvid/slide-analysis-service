import re

import pypdfium2 as pdfium


def get_context_snippet(text_page: pdfium.PdfTextPage, char_index: int, radius: int = 50) -> str:
    """
    Gets the context of the current line of text. Adds '...' if the line was truncated because of the radius.
    """
    total_chars = text_page.count_chars()

    start_idx = max(0, char_index - radius)
    end_idx = min(total_chars, char_index + radius + 1)

    text_before = text_page.get_text_range(start_idx, char_index - start_idx)
    target_char = text_page.get_text_range(char_index, 1)
    text_after = text_page.get_text_range(char_index + 1, end_idx - char_index - 1)

    # Process the preceding text.
    parts_before = re.split(r"\r\n|\n|\r", text_before)
    line_start_text = parts_before[-1]

    # Check the prefix: if no line break was found and we are not at the start of the document.
    prefix = "..." if len(parts_before) == 1 and start_idx > 0 else ""

    # Process the following text.
    parts_after = re.split(r"\r\n|\n|\r", text_after)
    line_end_text = parts_after[0]

    # Check the suffix: if no line break was found and we are not at the end of the document.
    suffix = "..." if len(parts_after) == 1 and end_idx < total_chars else ""

    # Assemble the snippet.
    snippet = f"{prefix}{line_start_text}[{target_char}]{line_end_text}{suffix}"

    # Normalise whitespace.
    return " ".join(snippet.split())


def extract_lines_from_text_page(text_page: pdfium.PdfTextPage) -> list[str]:
    """
    Extracts and processes the individual lines of text from a text page object.
    """
    lines: list[str] = []

    rect_count = text_page.count_rects()
    for rect_index in range(rect_count):
        left, bottom, right, top = text_page.get_rect(rect_index)
        rect_text = text_page.get_text_bounded(left=left, bottom=bottom, right=right, top=top)
        if not rect_text:
            continue

        for raw_line in rect_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            line = " ".join(raw_line.split())
            if line:
                lines.append(line)

    return lines

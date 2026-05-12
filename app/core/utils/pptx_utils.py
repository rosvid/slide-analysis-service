import logging

from pptx.oxml.text import CT_TextParagraphProperties as TextParagraphProperties
from pptx.slide import SlideMaster

logger = logging.getLogger(__name__)


def has_non_bullet(text_paragraph_properties: TextParagraphProperties) -> bool:
    return bool(text_paragraph_properties.xpath("./a:buAutoNum | ./a:buNone"))


def has_bullet(text_paragraph_properties: TextParagraphProperties) -> bool:
    return bool(text_paragraph_properties.xpath("./a:buBlip | ./a:buChar"))


def has_placeholder_non_bullets_at_level(placeholder, level) -> bool:
    return placeholder.element.xpath(f".//a:lvl{level + 1}pPr/a:buAutoNum | .//a:lvl{level + 1}pPr/a:buNone")


def has_placeholder_bullets_at_level(placeholder, level) -> bool:
    return placeholder.element.xpath(f".//a:lvl{level + 1}pPr/a:buChar | .//a:lvl{level + 1}pPr/a:buBlip")


def has_master_bullets_at_level(master: SlideMaster, level) -> bool:
    return master.element.xpath(f".//p:txStyles/p:bodyStyle/a:lvl{level + 1}pPr/a:buChar | .//p:txStyles/p:bodyStyle/a:lvl{level + 1}pPr/a:buBlip")


def get_body_style_from_master(master: SlideMaster):
    """Retrieve the body text style from the slide master."""

    buChar_level1 = master.element.xpath(".//p:txStyles/p:bodyStyle/a:lvl1pPr/a:buChar")
    buChar_level2 = master.element.xpath(".//p:txStyles/p:bodyStyle/a:lvl2pPr/a:buChar")
    buChar_level3 = master.element.xpath(".//p:txStyles/p:bodyStyle/a:lvl3pPr/a:buChar")
    buChar_level4 = master.element.xpath(".//p:txStyles/p:bodyStyle/a:lvl4pPr/a:buChar")
    buChar_level5 = master.element.xpath(".//p:txStyles/p:bodyStyle/a:lvl5pPr/a:buChar")
    buChar_level6 = master.element.xpath(".//p:txStyles/p:bodyStyle/a:lvl6pPr/a:buChar")
    buChar_level7 = master.element.xpath(".//p:txStyles/p:bodyStyle/a:lvl7pPr/a:buChar")
    buChar_level8 = master.element.xpath(".//p:txStyles/p:bodyStyle/a:lvl8pPr/a:buChar")
    buChar_level9 = master.element.xpath(".//p:txStyles/p:bodyStyle/a:lvl9pPr/a:buChar")

    # Print information if buchar levels are found.
    logger.info("Body Style Bullet Characters:")
    for i, buChar in enumerate([buChar_level1, buChar_level2, buChar_level3, buChar_level4,
                                buChar_level5, buChar_level6, buChar_level7,
                                buChar_level8, buChar_level9], start=1):
        if buChar:
            logger.info(f"Level {i} buChar: {buChar[0].get('char')}")

    return None


# checks if shape has <p:txBody> element with <a:listStyle> child
def shape_has_bullets(shape) -> bool:
    if not shape.element.xpath(".//p:txBody"):
        return False

    list_style = shape.element.xpath(".//p:txBody/a:listStyle")
    return len(list_style) > 0

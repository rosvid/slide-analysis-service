import enum
from django.utils.translation import gettext_lazy as _


class RuleId(enum.Enum):
    """
    Enum representing the unique identifiers for various rules used in presentation slides analysis.

    When a new rule file is implemented, it should be added to this enum.
    """
    def __init__(self, description):
        self._value_ = self.name
        self.description = description

    LAYOUT_CONTRAST_RATIO = _("The minimum level of conformance for contrast ratio between text and background colors (WCAG 2.2).")

    MEDIA_MAX_IMAGES_PER_SLIDE = _("The maximum number of images that can be used per slide in presentations.")
    MEDIA_MAX_ANIMATIONS_PER_SLIDE = _("The maximum number of animations that can be used per slide in presentations.")
    MEDIA_MIN_IMAGE_PPI = _("The minimum PPI (pixels per inch) that images should have in presentations.")

    TEXT_MAX_WORDS_PER_ROW = _("The maximum number of words per row that can be used in slides.")
    TEXT_MAX_WORDS_PER_SLIDE = _("The maximum number of words per slide that can be used in presentations.")
    TEXT_MAX_BULLET_POINTS_PER_SLIDE = _("The maximum number of bullet points per slide that can be used in presentations.")
    TEXT_MAX_FONTS = _("The maximum number of fonts that can be used in presentations.")
    TEXT_MIN_FONT_SIZE = _("The minimum font size that can be used in presentations.")

    def __str__(self):
        return self.value

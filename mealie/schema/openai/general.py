from pydantic import BaseModel, Field

from ._base import OpenAIBase


class OpenAIText(OpenAIBase):
    text: str = Field(..., description="A simple response message")


class OpenAIFoodTranslationItem(BaseModel):
    en: str = Field(..., description="The exact original English ingredient name")
    jp: str = Field(..., description="Japanese ingredient name in hiragana or katakana")
    jpKanji: str = Field("", description="Japanese ingredient name including kanji when available, else empty")


class OpenAIFoodTranslations(OpenAIBase):
    translations: list[OpenAIFoodTranslationItem] = Field(
        default_factory=list,
        description="Translated ingredient names in the same order as input",
    )

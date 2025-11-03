import unicodedata
from typing import Literal
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.domain.services import BaseService

base_service = BaseService()

RANGES = {
    "georgian": [(0x10A0,0x10FF),(0x2D00,0x2D2F),(0x1C90,0x1CBF)],
    "cyrillic": [(0x0400,0x04FF),(0x0500,0x052F),(0x2DE0,0x2DFF),(0xA640,0xA69F)],
    "greek": [(0x0370,0x03FF),(0x1F00,0x1FFF)],
    "armenian": [(0x0530,0x058F),(0xFB13,0xFB17)],
    "arabic": [(0x0600,0x06FF),(0x0750,0x077F),(0x08A0,0x08FF)],
    "hebrew": [(0x0590,0x05FF)],
    "devanagari": [(0x0900,0x097F)],
    "thai": [(0x0E00,0x0E7F)],
    "han": [(0x4E00,0x9FFF),(0x3400,0x4DBF)],
    "hiragana": [(0x3040,0x309F)],
    "katakana": [(0x30A0,0x30FF)],
    "hangul": [(0xAC00,0xD7AF),(0x1100,0x11FF)],
    "latin": [(0x0041,0x007A),(0x00C0,0x00FF),(0x0100,0x017F),(0x0180,0x024F),(0x1E00,0x1EFF)],
}

def in_ranges(cp, ranges):
    for a,b in ranges:
        if a <= cp <= b:
            return True
    return False

def classify_char(ch):
    cp = ord(ch)
    cat = unicodedata.category(ch)
    if cat[0] in {"P","S","Z","C","N"}:
        return None
    for lang, ranges in RANGES.items():
        if in_ranges(cp, ranges):
            return lang
    name = unicodedata.name(ch, "")
    if "CJK UNIFIED IDEOGRAPH" in name:
        return "han"
    return "other"

def distribution(text):
    counts = {k:0 for k in RANGES.keys()}
    total = 0
    for ch in text:
        lang = classify_char(ch)
        if not lang:
            continue
        counts[lang] = counts.get(lang,0) + 1
        total += 1
    perc = {k:v/total for k,v in counts.items() if total>0 and v>0}
    return counts, perc, total

def longest_runs(text):
    best = {}
    prev = None
    run = 0
    for ch in text:
        lang = classify_char(ch)
        if not lang or lang in ("georgian","latin"):
            if prev and prev not in ("georgian","latin"):
                best[prev] = max(best.get(prev,0), run)
            prev = None
            run = 0
            continue
        if lang == prev:
            run += 1
        else:
            if prev and prev not in ("georgian","latin"):
                best[prev] = max(best.get(prev,0), run)
            prev = lang
            run = 1
    if prev and prev not in ("georgian","latin"):
        best[prev] = max(best.get(prev,0), run)
    return best

def first_appearance_order(text):
    order = {}
    for ch in text:
        lang = classify_char(ch)
        if lang and lang not in order:
            order[lang] = len(order)
    return order

def needtranslate(text, min_ge=0.15):
    counts, perc, _ = distribution(text)
    if not perc:
        return False, "georgian", []

    ge = perc.get("georgian", 0.0)
    en = perc.get("latin", 0.0)
    others = [k for k in perc if k not in ("georgian", "latin", "other")]

    if ge == 0:
        return False, "georgian", []

    if ge >= min_ge and not others:
        return False, "georgian", []

    if ge >= min_ge and others:
        return True, "georgian", others

    return False, "georgian", others

class LanguageDetectorOutput(BaseModel):
    language: Literal["georgian", "english", "russian", "french", "german", "italian", "spanish", "portuguese", "turkish", "armenian", 'other'] = Field(
        description="The detected language of the input text"
    )

    if_other_then_which_language: str | None = Field(
        default=None,
        description="If the 'language' field has the value 'other', specify the language here. Otherwise, leave this field empty."
    )

language_detector_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=base_service.get_gemini_key()
).with_structured_output(LanguageDetectorOutput)

def validate_language_output(output) -> bool:
    try:
        if isinstance(output, LanguageDetectorOutput):
            validated_output = output
        else:
            validated_output = LanguageDetectorOutput.model_validate(output)
        
        if validated_output.language == 'other' and not validated_output.if_other_then_which_language:
            return False
        
        if validated_output.language != 'other' and validated_output.if_other_then_which_language:
            return False
        
        return True
        
    except Exception:
        return False


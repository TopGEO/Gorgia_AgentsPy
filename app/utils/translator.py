import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.config.settings import settings
from .language_detector import needtranslate
from pydantic import BaseModel, Field

class TranslationOutput(BaseModel):
    translated_text: str = Field(description="The translated text in the target language")
    reason: str = Field(description="Brief explanation of translation decisions or challenges")

def _format_lang_list(langs: list[str]) -> str:
    n = len(langs)
    if n == 0:
        return ""
    if n == 1:
        return langs[0]
    if n == 2:
        return f"{langs[0]} and {langs[1]}"
    return ", ".join(langs[:-1]) + f", and {langs[-1]}"

async def translate(msg: str, arg: tuple) -> str:
    need_translate, target_lang, other_langs = arg
    if not need_translate:
        return msg

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.gemini_api_key,
        temperature=0
    )

    structured_llm = llm.with_structured_output(TranslationOutput)

    others_str = _format_lang_list(other_langs)
    hint = (
        f"This message contains text written in multiple languages: {others_str}. "
        f"Your task is to carefully identify ANY text, words, or even individual characters that are NOT in {target_lang}, "
        f"and translate them into proper {target_lang}. "
        f"Pay special attention to mixed scripts, Cyrillic characters, and any non-{target_lang} content embedded within {target_lang} text. "
        f"Preserve the original structure and formatting while ensuring ALL content is in {target_lang}."
        if others_str
        else f"Translate the following text into {target_lang}. Ensure all content is properly translated and maintains the original structure."
    )

    translation_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", hint),
            ("human", "{text}"),
        ]
    )

    try:
        chain = translation_prompt | structured_llm
        result = await chain.ainvoke({"text": msg})

        if result is None:
            print(f"⚠️ Translation failed: LLM returned None for message: {msg[:10000]}...")
            return msg

        print(f"\n🈳 Translated message:\n\"\"\"\n{msg}\n\"\"\"\n:\n\"\"\"{result.translated_text}\"\"\"\n📝 Reason: {result.reason}\n\n")
        return result.translated_text
    except Exception as e:
        print(f"❌ Translation error: {e}. Returning original message: {msg[:10000]}...")
        return msg

async def translate_if_needed(text: str) -> str:
    translation_result = needtranslate(text)
    print(f"🔍 Translation check result: {translation_result}")
    return await translate(text, translation_result)
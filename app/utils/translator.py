import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config.settings import settings
from .language_detector import needtranslate

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
        google_api_key=settings.gemini_api_key
    )

    others_str = _format_lang_list(other_langs)
    hint = (
        f"The message includes text in {others_str}. "
        f"Translate all non-{target_lang} content into {target_lang}."
        if others_str
        else f"Translate the following text to {target_lang}."
    )

    translation_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", hint),
            ("human", "{text}"),
        ]
    )

    chain = translation_prompt | llm | StrOutputParser()
    translated = await chain.ainvoke({"text": msg})
    logging.info(f"\n🈳 Translated message:\n\"\"\"\n{msg}\n\"\"\"\n to {target_lang}:\n\"\"\"{translated}\"\"\"\n\n")
    return translated

async def translate_if_needed(text: str) -> str:
    translation_result = needtranslate(text)
    return await translate(text, translation_result)
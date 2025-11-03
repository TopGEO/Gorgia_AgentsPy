from tkinter.messagebox import QUESTION
import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from scrape_embed.elite_embed import List

headers={"User-Agent": "python-httpx", "Accept-Language": "en"}
response = requests.get("https://api.zoommer.ge/v1/Categories/all-categories", headers=headers)

ids_and_names = []
for item in response.json():
    ids_and_names.append({"id": item["id"], "name": item["name"]})

question = "What brands of mobiles do we have?"

prompt = ChatPromptTemplate.from_messages([
    ("system", f"Your only mission is to return id of the category from <categories> tag that best matches the user question.\n<categories>{ids_and_names}</categories>"),
    ("user", question)
]).with_structured_output(
    {"category_id": List[str]},
    """You must only return the id of the category as a string, nothing else. 
    If you can't find a good match, return "unknown".""",
    validate=True
)

llm = ChatOpenAI(model="gpt-4.1")

output_parser = StrOutputParser()

chain = prompt | llm | output_parser

response = chain.invoke({"question": "What is the capital of France?"})

print(response)
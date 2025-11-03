from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from pathlib import Path


def split_document_and_add_metadatas_to_chunks(document_content_str:str, additional_metadata: dict, text_splitter: RecursiveCharacterTextSplitter):
    chunks = text_splitter.split_text(document_content_str)
    result = []
    for c in chunks:
        additional_metadata['content'] = c
        result.append(
            {
                "metadata": {**additional_metadata},
                "content" : c
            }
        )
    return result



def read_txt_files_add_filename_metadata_and_return_chunks(base_path: str, text_splitter: RecursiveCharacterTextSplitter):
    all_chunks = []
    
    txt_files = Path(base_path).glob("*.txt")
    
    for file_path in txt_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        

        metadata = {
            "filename": file_path.name,
            "file_path": str(file_path)
        }
        
        chunks = split_document_and_add_metadatas_to_chunks(
            document_content_str=content,
            additional_metadata=metadata,
            text_splitter=text_splitter
        )
        
        all_chunks.extend(chunks)
    
    return all_chunks


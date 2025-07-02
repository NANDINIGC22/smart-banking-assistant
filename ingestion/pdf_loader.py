import os
import fitz  # PyMuPDF
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import Image
import chromadb
from langchain_community.embeddings import OpenAIEmbeddings
from graph_loader import create_fulltext_index
from neo4j import GraphDatabase
from dotenv import load_dotenv
load_dotenv()

def process_pdfs(pdf_paths):
    vectordb = chromadb.PersistentClient(path="vectordb")
    collection = vectordb.get_or_create_collection(name="banking_policies")

    embedder = OpenAIEmbeddings()

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )

    for path in pdf_paths:
        pdf_name = os.path.basename(path)
        doc = fitz.open(path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text().strip()

            # Improved image chunking: check low word count or empty text, fallback to OCR
            if not text or len(text.split()) < 5:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # High-res image for OCR
                img_path = f"temp_page_{page_num}.png"
                pix.save(img_path)

                img = Image.open(img_path).convert("RGB")
                text = pytesseract.image_to_string(img, lang="eng")
                os.remove(img_path)

            text = text.strip()
            if text:
                embedding = embedder.embed_query(text)
                collection.add(
                    documents=[text],
                    embeddings=[embedding],
                    metadatas=[{"source": pdf_name}],
                    ids=[f"{pdf_name}_{page_num}"]
                )

    print("PDF ingestion completed.")
    create_fulltext_index(driver)

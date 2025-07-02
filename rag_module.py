# ✅ Final Clean rag_module.py for RAGAS 0.2.15 with Source Fix and Debugging

import os
from llm_selector import get_llm
import chromadb
from neo4j import GraphDatabase
#from ragas.evaluation import evaluate
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()

def get_rag_response(query, model_name):
    vectordb = chromadb.PersistentClient(path="vectordb")
    collection = vectordb.get_or_create_collection(name="banking_policies")

    embedder = OpenAIEmbeddings()
    query_embedding = embedder.embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    source_pdf = None
    if results and "metadatas" in results and results["metadatas"]:
       first_meta = results["metadatas"][0]
       if first_meta and isinstance(first_meta, list) and len(first_meta) > 0:
        source_pdf = first_meta[0].get("source")
    print(f"Full Metadata Results: {results.get('metadatas')}")    

    #source_pdf = None
    #if results and "metadatas" in results and results["metadatas"]:
        #if results["metadatas"][0] and isinstance(results["metadatas"][0], dict):
           # source_pdf = results["metadatas"][0].get("source")

    chunks = results["documents"][0] if results["documents"] else []
    context_text = " ".join(chunks)

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    with driver.session() as session:
        graph_results = session.run(
            """
            CALL db.index.fulltext.queryNodes('DocIndex', $q) YIELD node, score
            RETURN node.content AS section_text, score
            ORDER BY score DESC
            LIMIT 5
            """,
            q=query
        )
        graph_contexts = [record["section_text"] for record in graph_results]

    full_context = context_text + " ".join(graph_contexts)

    llm = get_llm(model_name)
    prompt = f"Answer the question based on the following context:\n{full_context}\nQuestion: {query}"
    response = llm(prompt)

    return response, graph_contexts, source_pdf

    #def ragas_score(query, answer, contexts):
    #    print(f"Question: {query}")
    #    print(f"Answer: {answer}")
     #   print(f"Contexts: {contexts}")

     #   try:
     #       scores = evaluate(query, answer, contexts)
     #       print(f"RAGAS Raw Scores: {scores}")
     #       retrieval = scores.get("retrieval", 0.0)
     #       faithfulness = scores.get("faithfulness", 0.0)
     #       relevance = scores.get("answer_relevance", 0.0)
     #       return retrieval, faithfulness, relevance
     #   except Exception as e:
     #       print(f"RAGAS scoring error: {e}")
     #       return 0.0, 0.0, 0.0

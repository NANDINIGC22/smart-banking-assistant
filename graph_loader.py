# ✅ Final Clean graph_loader.py with Correct create_fulltext_index Signature

from neo4j import GraphDatabase

def process_graph_docs(docs, driver):
    with driver.session() as session:
        for doc in docs:
            content = doc.page_content.strip()
            metadata = doc.metadata
            if not content:
                continue

            name = metadata.get("name", "Unknown")
            chunk_id = metadata.get("chunk_id", name)

            session.run(
                """
                MERGE (d:Document {chunk_id: $chunk_id})
                SET d.content = $content, d.name = $name
                """,
                {"chunk_id": chunk_id, "content": content, "name": name}
            )

def create_fulltext_index(driver):
    with driver.session() as session:
        session.run("CREATE FULLTEXT INDEX DocIndex IF NOT EXISTS FOR (d:Document) ON EACH [d.content]")

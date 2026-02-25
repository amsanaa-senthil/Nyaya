from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from graph.neo4j_loader import normalize_title


# 🔥 ADD THIS
load_dotenv()


class CitationGraph:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )

    def get_case_info(self, case_name):
        normalized = normalize_title(case_name)
        if not normalized:
            return None
        query = """
        MATCH (c:Case {title: $title})
        OPTIONAL MATCH (c)<-[:CITES]-(other)
        RETURN c.title AS case, count(other) AS citation_count
        """

        with self.driver.session() as session:
            result = session.run(query, title=normalized)
            return result.single()

    def get_most_cited(self, limit=10):
        query = """
        MATCH (c:Case)
        WITH c, COUNT { (c)<-[:CITES]-() } AS citations
        WHERE citations > 0
        RETURN c.title AS case, citations
        ORDER BY citations DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [(r["case"], r["citations"]) for r in result]

    def get_cited_cases(self, case_name, limit=20):
        normalized = normalize_title(case_name)
        if not normalized:
            return []

        query = """
        MATCH (source:Case {title: $title})-[:CITES]->(cited:Case)
        RETURN cited.title AS case
        ORDER BY cited.title
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, title=normalized, limit=limit)
            return [r["case"] for r in result]

    def get_cited_by(self, case_name, limit=20):
        normalized = normalize_title(case_name)
        if not normalized:
            return []

        query = """
        MATCH (cited:Case {title: $title})<-[:CITES]-(source:Case)
        RETURN source.title AS case
        ORDER BY source.title
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, title=normalized, limit=limit)
            return [r["case"] for r in result]

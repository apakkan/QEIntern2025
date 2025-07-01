from langchain_neo4j import Neo4jGraph
import os

graph = Neo4jGraph(
    url=os.getenv('NEO4J_URI'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

def get_related_entities(story_number):
    query = """
    MATCH (r:Requirement {story_number: $story_number})-[:RELATED_TO]->(e)
    RETURN e
    """
    results = graph.query(query, {"story_number": story_number})
    return results

# After creating a node in Neo4j
result = graph.query(
    "CREATE (r:Requirement {story_number: $story_number, ...}) RETURN id(r) AS node_id",
    {"story_number": story_number}
)
kg_node_id = result[0]['node_id']
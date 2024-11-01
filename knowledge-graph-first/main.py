# Initialize the knowledge graph
knowledge_graph = {
    "nodes": [],
    "edges": []
}

# Function to add a node
def add_node(graph, node_id, label, properties=None):
    if properties is None:
        properties = {}
    graph["nodes"].append({
        "id": node_id,
        "label": label,
        "properties": properties
    })

# Function to add an edge
def add_edge(graph, source_id, target_id, relationship):
    graph["edges"].append({
        "source": source_id,
        "target": target_id,
        "relationship": relationship
    })

# Add nodes to the knowledge graph
add_node(knowledge_graph, "1", "Person", {"name": "John Doe", "age": 30})
add_node(knowledge_graph, "2", "Person", {"name": "Jane Smith", "age": 25})
add_node(knowledge_graph, "3", "Movie", {"title": "The Matrix", "year": 1999})
add_node(knowledge_graph, "4", "Movie", {"title": "Inception", "year": 2010})

# Add relationships between nodes
add_edge(knowledge_graph, "1", "3", "WATCHED")
add_edge(knowledge_graph, "2", "4", "WATCHED")
add_edge(knowledge_graph, "1", "2", "FRIEND")

# Print the knowledge graph
print("Knowledge Graph Nodes:")
for node in knowledge_graph["nodes"]:
    print(f"ID: {node['id']}, Label: {node['label']}, Properties: {node['properties']}")

print("\nKnowledge Graph Edges:")
for edge in knowledge_graph["edges"]:
    print(f"Source: {edge['source']}, Target: {edge['target']}, Relationship: {edge['relationship']}")

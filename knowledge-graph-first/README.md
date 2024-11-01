# Knowledge Graph

A knowledge graph is a networked representation of structured data that links entities (people, places, things) and their relationships in a way that makes data interconnected, searchable, and meaningful. Knowledge graphs are widely used for applications to provide more relevant and contextualized answers.

- Entities (Nodes): Objects or concepts in the graph, like "Person," "Place," or "Event."
- Relations (Edges): Connections that link entities and define their relationships, like "works at," "married to," or "located in."
- Attributes: Properties or details about entities, such as the age of a person or the population of a city.

## Usage
`main.py` - basic knowledge graph with no dependencies
- `python main.py`

`neo4j_example.py` - basic knowledge graph with actual graph database Neo4j via neomodel
- `poetry install`
- `docker run --restart always --publish=7474:7474 --publish=7687:7687 neo4j:5.25.1` (run neo4j locally)
- open [http://localhost:7474/browser/](http://localhost:7474/browser/)
- login with username/password `neo4j/neo4j` and update script `neo4j_example.py` with your password
- `poetry run neo4j_example.py`

`spacy_example.py` - extract entities and intents from user queries about movies via spaCy NLP toolkit
- `poetry install`
- `python -m spacy download en_core_web_sm` (download language model)
- `poetry run spacy_example.py`

spaCy is a free open-source library for Natural Language Processing in Python. It features NER, POS tagging, dependency parsing, word vectors and more.

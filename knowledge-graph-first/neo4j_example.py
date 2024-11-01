from neomodel import (config, StructuredNode, StringProperty, IntegerProperty, 
                      RelationshipTo, StructuredRel, db, DoesNotExist)

#==========================
#  CONSTANTS
#==========================
password = "flowereagle1"  # Update with your Neo4j password

#==========================
#  SETUP
#==========================
# Set up the connection to the Neo4j database
config.DATABASE_URL = f"bolt://neo4j:{password}@localhost:7687"


#==========================
#  MAIN
#==========================
# Define a Relationship Model
class WatchedRel(StructuredRel):
    rating = IntegerProperty()

# Define Node Models
class Person(StructuredNode):
    name = StringProperty(unique_index=True)
    age = IntegerProperty()
    # Relationship to Movie node
    watched = RelationshipTo('Movie', 'WATCHED', model=WatchedRel)

class Movie(StructuredNode):
    title = StringProperty(unique_index=True)
    year = IntegerProperty()

# Clear the database for a fresh start
def clear_database():
    db.cypher_query("MATCH (n) DETACH DELETE n")

# Seed the database with nodes and relationships
def seed_database():
    # Create Person nodes
    john = Person(name="John Doe", age=30).save()
    jane = Person(name="Jane Smith", age=25).save()

    # Create Movie nodes
    matrix = Movie(title="The Matrix", year=1999).save()
    inception = Movie(title="Inception", year=2010).save()

    # Create relationships
    john.watched.connect(matrix, {'rating': 5})
    jane.watched.connect(inception, {'rating': 4})
    john.watched.connect(inception, {'rating': 3})

    print("Database seeded with sample data.")

def create_person_with_five_star_ratings(name, age, movie_titles):
    """
    ORM to add a person with 5-star ratings for watched movies.
    """
    try:
        # Try to get the person by name and age
        person = Person.nodes.get(name=name, age=age)
    except DoesNotExist:
        # If person does not exist, create a new one
        person = Person(name=name, age=age)
        person.save()

    # Create or update the relationship with each movie, setting rating to 5
    for title in movie_titles:
        # Find the movie by title
        movie = Movie.nodes.get_or_none(title=title)
        if movie:
            # Create or update the relationship
            person.watched.connect(movie, {'rating': 5})
        else:
            print(f"Movie '{title}' does not exist in the database.")


def add_person_with_four_star_ratings(name, age, movie_titles):
    """
    RAW QUERY to add a person with 4-star ratings for watched movies.
    """
    # Construct the Cypher query
    query = """
    MERGE (p:Person {name: $name, age: $age})
    WITH p
    UNWIND $movies AS movie_title
    MATCH (m:Movie {title: movie_title})
    MERGE (p)-[r:WATCHED]->(m)
    SET r.rating = 4
    RETURN p, m, r
    """
    
    # Parameters for the query
    params = {
        "name": name,
        "age": age,
        "movies": movie_titles
    }
    
    # Execute the query
    results, meta = db.cypher_query(query, params)
    print("Query executed. Relationships created with 5-star ratings.")

# Query the database
def query_database():
    # Query all persons who watched a movie
    for person in Person.nodes:
        for movie in person.watched:
            print(f"{person.name} watched {movie.title} with rating {person.watched.relationship(movie).rating}")
    print()

    # Query specific person details
    john = Person.nodes.get(name="John Doe")
    print(f"\nDetails of {john.name}:")
    for movie in john.watched:
        rel = john.watched.relationship(movie)
        print(f"- Watched {movie.title} ({movie.year}) with rating {rel.rating}")
    print()

    # Retrieve All Persons and Their Movies Watched
    print("Retrieve All Persons and Their Movies Watched")
    query = """
    MATCH (p:Person)-[r:WATCHED]->(m:Movie)
    RETURN p.name AS person, p.age AS age, m.title AS movie, m.year AS year, r.rating AS rating
    """
    results, meta = db.cypher_query(query)
    for record in results:
        print(f"{record[0]} (age {record[1]}) watched {record[2]} ({record[3]}) with rating {record[4]}")
    print()

    # Find Movies Watched by a Specific Person
    print("Find Movies Watched by a Specific Person")
    person_name = "John Doe"
    query = """
    MATCH (p:Person {name: $person_name})-[r:WATCHED]->(m:Movie)
    RETURN m.title AS movie, m.year AS year, r.rating AS rating
    """
    results, meta = db.cypher_query(query, {"person_name": person_name})
    for record in results:
        print(f"{person_name} watched {record[0]} ({record[1]}) with rating {record[2]}")
    print()

    # Count Movies Each Person Has Watched
    print("Count Movies Each Person Has Watched")
    query = """
    MATCH (p:Person)-[:WATCHED]->(m:Movie)
    RETURN p.name AS person, COUNT(m) AS movies_watched
    ORDER BY movies_watched DESC
    """
    results, meta = db.cypher_query(query)
    for record in results:
        print(f"{record[0]} has watched {record[1]} movies")
    print()

    # Find the Highest Rated Movies Watched by Each Person
    print("Find the Highest Rated Movies Watched by Each Person")
    query = """
    MATCH (p:Person)-[r:WATCHED]->(m:Movie)
    WITH p, MAX(r.rating) AS max_rating
    MATCH (p)-[r:WATCHED]->(m:Movie)
    WHERE r.rating = max_rating
    RETURN p.name AS person, m.title AS movie, r.rating AS rating
    ORDER BY p.name
    """
    results, meta = db.cypher_query(query)
    for record in results:
        print(f"{record[0]}'s highest-rated movie is {record[1]} with a rating of {record[2]}")
    print()

    # List All Persons Who Watched a Specific Movie
    print("List All Persons Who Watched a Specific Movie")
    movie_title = "Inception"
    query = """
    MATCH (p:Person)-[r:WATCHED]->(m:Movie {title: $movie_title})
    RETURN p.name AS person, r.rating AS rating
    ORDER BY r.rating DESC
    """
    results, meta = db.cypher_query(query, {"movie_title": movie_title})
    for record in results:
        print(f"{record[0]} watched {movie_title} with a rating of {record[1]}")
    print()

    # Average Rating of Each Movie
    print("Average Rating of Each Movie")
    query = """
    MATCH (p:Person)-[r:WATCHED]->(m:Movie)
    RETURN m.title AS movie, AVG(r.rating) AS average_rating
    ORDER BY average_rating DESC
    """
    results, meta = db.cypher_query(query)
    for record in results:
        print(f"The movie {record[0]} has an average rating of {record[1]:.2f}")
    print()

    # Find Persons Who Rated All Their Movies 5 Stars
    print("Find Persons Who Rated All Their Movies 5 Stars")
    query = """
    MATCH (p:Person)-[r:WATCHED]->(m:Movie)
    WITH p, COLLECT(r.rating) AS ratings
    WHERE ALL(rate IN ratings WHERE rate = 5)
    RETURN p.name AS person
    """
    results, meta = db.cypher_query(query)
    for record in results:
        print(f"{record[0]} rated all watched movies 5 stars")
    print()


# Main function to run the script
if __name__ == "__main__":
    clear_database()      # Clear the database (use with caution!)
    seed_database()       # Seed the database with nodes and relationships
    create_person_with_five_star_ratings("Alice", 28, ["The Matrix", "Inception"])
    add_person_with_four_star_ratings("Amelia", 5, ["The Matrix", "Inception"])
    query_database()      # Query and display results

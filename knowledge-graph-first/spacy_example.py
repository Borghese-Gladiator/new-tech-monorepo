"""
spaCy code to extract entities and intents from user queries about movies
"""
import spacy
from spacy.matcher import Matcher


#==========================
#  DOWNLOAD
#==========================
# Load downloaded language model
nlp = spacy.load("en_core_web_sm")


#==========================
#  CONSTANTS
#==========================
# Initialize the matcher for intent recognition
matcher = Matcher(nlp.vocab)


#==========================
#  SETUP
#==========================
# Define movie-related intents using matching patterns
pattern_movie_info = [{"LOWER": "tell"}, {"LOWER": "me"}, {"LOWER": "about"}, {"ENT_TYPE": "WORK_OF_ART"}]
pattern_actor_info = [{"LOWER": "who"}, {"LOWER": "is"}, {"ENT_TYPE": "PERSON"}]
pattern_genre_movies = [{"LOWER": "show"}, {"LOWER": "me"}, {"TEXT": "movies"}, {"TEXT": "in"}, {"TEXT": "genre"}]

# Add patterns to the matcher
matcher.add("MOVIE_INFO", [pattern_movie_info])
matcher.add("ACTOR_INFO", [pattern_actor_info])
matcher.add("GENRE_MOVIES", [pattern_genre_movies])


#==========================
#  MAIN
#==========================
# Sample queries to analyze
queries = [
    "Tell me about Inception",
    "Who is Leonardo DiCaprio?",
    "Show me movies in the Sci-Fi genre"
]

# Process each query to identify intents and extract entities
for query in queries:
    doc = nlp(query)

    # Check for intent using the matcher
    matches = matcher(doc)
    if matches:
        for match_id, start, end in matches:
            intent = nlp.vocab.strings[match_id]
            print(f"Query: {query}")
            print(f"Identified Intent: {intent}")

            # Extract entities based on intent
            if intent == "MOVIE_INFO":
                movie = [ent.text for ent in doc.ents if ent.label_ == "WORK_OF_ART"]
                if movie:
                    print(f"Movie: {movie[0]}")
            
            elif intent == "ACTOR_INFO":
                person = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
                if person:
                    print(f"Actor: {person[0]}")
            
            elif intent == "GENRE_MOVIES":
                genre = [ent.text for ent in doc if ent.ent_type_ == "GENRE"]
                if genre:
                    print(f"Genre: {genre[0]}")

    print("-" * 40)

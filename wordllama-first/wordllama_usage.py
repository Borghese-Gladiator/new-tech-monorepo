"""
WordLLama general usage
"""
from wordllama import WordLlama

#=====================
#  CONSTANTS
#=====================
wl = WordLlama.load()
candidates = ["I went to the park", "I went to the shop", "I went to the truck", "I went to the vehicle"]

#=====================
#  USAGE
#=====================

# EMBEDDING TEXT
print("EMBEDDING TEXT")
embeddings = wl.embed(["The quick brown fox jumps over the lazy dog", "And all that jazz"])
print(embeddings.shape)  # Output: (2, 64)
print()

# CALCULATING SIMILARITY
print("CALCULATING SIMILARITY")
similarity_score = wl.similarity("I went to the car", "I went to the pawn shop")
print(similarity_score)  # Output: e.g., 0.0664
print()


# RANKING DOCUMENTS
print("RANKING DOCUMENTS")
query = "I went to the car"
ranked_docs = wl.rank(query, candidates, sort=True, batch_size=64)
print(ranked_docs)
print()
# Output:
# [
#   ('I went to the vehicle', 0.7441),
#   ('I went to the truck', 0.2832),
#   ('I went to the shop', 0.1973),
#   ('I went to the park', 0.1510)
# ]


# FUZZY DEDUPLICATION  - remove duplicate texts based on similarity threshold
print("FUZZY DEDUPLICATION")
deduplicated_docs = wl.deduplicate(candidates, return_indices=False, threshold=0.5)
print(deduplicated_docs)
print()
# Output:
# ['I went to the park',
#  'I went to the shop',
#  'I went to the truck']

# CLUSTERING - cluster documents into groups using KMeans clustering
print("CLUSTERING")
labels, inertia = wl.cluster(candidates, k=3, max_iterations=100, tolerance=1e-4, n_init=3)
print(labels, inertia)
print()
# Output:
# [2, 0, 1, 1], 0.4150

# FILTERING - Filter documents based on their similarity to a query
print("FILTERING")
filtered_docs = wl.filter(query, candidates, threshold=0.3)
print(filtered_docs)
print()
# Output:
# ['I went to the vehicle']


# TOP-K RETRIEVAL
print("TOP-K RETRIEVAL")
top_docs = wl.topk(query, candidates, k=2)
print(top_docs)
print()
# Output:
# ['I went to the vehicle', 'I went to the truck']


# SEMANTIC TEXT SPLITTING
print("SEMANTIC TEXT SPLITTING")
long_text = "Your very long text goes here... " * 100
chunks = wl.split(long_text, target_size=1536)
print(list(map(len, chunks)))
print()
# Output: [1055, 1055, 1187]
"""
The recommended target size is from 512 to 2048 characters, with the default size at 1536.
Chunks that need to be much larger should probably be batched after splitting, and will often be aggregated from multiple semantic chunks already.
"""


"""
from wordllama import WordLlama

# Load the default WordLlama model
wl = WordLlama.load()

# Calculate similarity between two sentences
similarity_score = wl.similarity("I went to the car", "I went to the pawn shop")
print(similarity_score)  # Output: e.g., 0.0664

# Rank documents based on their similarity to a query
query = "I went to the car"
candidates = ["I went to the park", "I went to the shop", "I went to the truck", "I went to the vehicle"]
ranked_docs = wl.rank(query, candidates)
print(ranked_docs)
# Output:
# [
#   ('I went to the vehicle', 0.7441),
#   ('I went to the truck', 0.2832),
#   ('I went to the shop', 0.1973),
#   ('I went to the park', 0.1510)
# ]
"""
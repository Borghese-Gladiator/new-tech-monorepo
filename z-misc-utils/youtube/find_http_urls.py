import re

# Input text
text = """
"""

# Regular expression to extract URLs
url_pattern = r"https?://[^\s]+"
url_list = re.findall(url_pattern, text)

# Output the extracted URLs
print(url_list)

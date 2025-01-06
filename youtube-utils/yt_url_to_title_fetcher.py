"""
Input: List of URLs
Output: Bulleted List of Titles + URLs
"""
import urllib.request
import json
import urllib.parse

url_list = []

output_str = ""
error_list = []

def get_yt_url(url: str):
    params = {"format": "json", "url": url}
    query_string = urllib.parse.urlencode(params)
    yt_url = f"https://www.youtube.com/oembed?{query_string}"

    with urllib.request.urlopen(yt_url) as response:
        response_text = response.read()
        data = json.loads(response_text.decode())
        return f"* {data['title']} - {url}\n"

for url in url_list:
    try:
        output_str += get_yt_url(url)
    except Exception as e:
        error_list.append(f"{url}: {e}")

print("**Successful URLs**\n")
print(output_str)

if error_list:
    print("\n**Failed URLs**\n")
    for error in error_list:
        print(error)
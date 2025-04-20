import requests
import base64
from markdown import markdown
from bs4 import BeautifulSoup
import re

request = requests.get(url='https://api.github.com/search/repositories?q=learn-database&order=desc&per-page=1')

response = request.json()
response = response['items']

def readme_preprocessing(readme):
    # Content decoding
    content = base64.b64decode(readme['content'])

    # Converting the markdown to html
    html = markdown(content)

    # Parse the html version of the readme
    soup = BeautifulSoup(html, "html.parser")

    # Parse the content of the html file
    content = soup.get_text()

    # Get the content in lines and paragraphs
    lines = (line.strip() for line in content.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    # Remove the escape patterns from the document
    escape_pattern = r'\\x[0-9a-fA-F]{2}'
    cleaned_text = re.sub(escape_pattern, '', text)
    cleaned_text = re.sub('#', '', cleaned_text)
    cleaned_text = cleaned_text.replace('\\n', "")

    # Return the cleaned version of the readme file
    return cleaned_text

for repo in response:
    print(f"Name: {repo['full_name']}")
    print(f"Description: {repo['description']}")
    print(f"URL: {repo['url']}")
    new_request = requests.get(url=("".join(repo['url']) + "/contents/README.md"))
    new_response = new_request.json()
    print(readme_preprocessing(new_response))
    break


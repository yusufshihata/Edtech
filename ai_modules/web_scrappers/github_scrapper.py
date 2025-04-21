import requests
import base64
from markdown import markdown
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import re

load_dotenv()
PAT = os.getenv("PAT")

class GithubFetcher:
    """A class organized by the builder pattern to fetch content from github."""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GithubFetcher, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {PAT}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_repos(self, topic, num_repos_per_page = 5):
        """This method gets the data of the repos related to this topic."""
        request = requests.get(url=f"https://api.github.com/search/repositories?q=learn-{topic}&order=desc&per-page={num_repos_per_page}", headers=self.headers)
        response = request.json()

        return response['items']

    def get_repo_content(self, repo):
        request = requests.get(url=("".join(repo['url']) + '/contents/README.md'), headers=self.headers)
        try:
            response = request.json()['content']
            return response
        except KeyError:
            return None

    def repo_formater(self, repo, content):
        return {"name": repo['name'], "description": repo['description'], "url": repo['url'], "content": content}

    def fetching(self, topic):
        repos = list()
        repos_data = self.get_repos(topic)

        for data in repos_data:
            print(data['url'])
            content = self.get_repo_content(data)
            repo = self.repo_formater(data, content)
            repos.append(repo)
        return repos

class ReadmePreprocessor:
    """A class organized by the builder pattern designed to preprocess the Readme.md files from github."""

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ReadmePreprocessor, cls).__new__(cls)
        return cls.instance
    
    def decoder(self, content):
        return base64.b64decode(content)

    def text_parser(self, content):
        html = markdown(content)
        soup = BeautifulSoup(html, "html.parser")

        content = soup.get_text()

        return content

    def formatter(self, content):
        lines = (line.strip() for line in content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        content = '\n'.join(chunk for chunk in chunks if chunk)
        return content

    def cleaner(self, content):
        patterns_to_remove = [r'\\x[0-9a-fA-F]{2}', '#', '\\n', '\\n-', '-']

        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content)
        return content

    def preprocessing(self, content):
        content = self.decoder(content)
        content = self.text_parser(content)
        content = self.formatter(content)
        content = self.cleaner(content)

        return content

def fetch_github_data(topic):
    data_fetcher = GithubFetcher()
    preprocessor = ReadmePreprocessor()

    fetched_repos = data_fetcher.fetching(topic)
    for repo in fetched_repos:
        if repo['content'] is not None:
            repo['content'] = preprocessor.preprocessing(repo['content'])
        else:
            continue

    return fetched_repos


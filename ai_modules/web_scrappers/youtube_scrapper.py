import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load .env module and define the API Key
load_dotenv()
API_KEY = os.getenv('API_KEY')

class YoutubeFetcher:
    """A class that fetches the youtube videos data."""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(YoutubeFetcher, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.youtube = build("youtube", "v3", developerKey=API_KEY)

    def search(self, topic):
        request = self.youtube.search().list(
            q=topic,
            part="snippet",
            type="video",
            safeSearch="strict"
        )

        response = request.execute()
        return response

    def format(self, videos):
        data = []
        for video in videos['items']:
            video_data = {
                "video_id": video['id']['videoId'],
                "title": video['snippet']['title'],
                "description": video['snippet']['description'],
                "publish_time": video['snippet']['publishedAt'],
                "thumbnail_url": video['snippet']['thumbnails']['high']['url'],
                "video_url": f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            }
            data.append(video_data)
        return data

    def fetch(self, topic):
        data = self.search(topic)
        data = self.format(data)
        return data


# Define the API function to use the fetcher
def fetch_youtube_data(topic):
    fetcher = YoutubeFetcher()
    videos = fetcher.fetch(topic)

    for idx, video in enumerate(videos):
        print(f"\nVideo {idx+1}")
        print(f"Title: {video['title']}")
        print(f"URL: {video['video_url']}")
        print(f"Description: {video['description'][:300]}...")

    return videos


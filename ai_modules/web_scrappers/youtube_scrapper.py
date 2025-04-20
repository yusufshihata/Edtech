from googleapiclient.discovery import build

# Replace this with your API key
API_KEY = "AIzaSyB7eqRjPjX-QztmumE_JAdnLEFXgFvQ1yQ"

# Initialize YouTube API client
youtube = build("youtube", "v3", developerKey=API_KEY)

def search_youtube(query, max_results=5):
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results,
        safeSearch="strict"
    )
    response = request.execute()
    
    results = []
    for item in response["items"]:
        video_data = {
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "channel_title": item["snippet"]["channelTitle"],
            "publish_time": item["snippet"]["publishedAt"],
            "thumbnail_url": item["snippet"]["thumbnails"]["high"]["url"],
            "video_url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        }
        results.append(video_data)
    
    return results

# Example usage
if __name__ == "__main__":
    topic = "Learn Reinforcement Learning"
    videos = search_youtube(topic)
    
    for idx, video in enumerate(videos):
        print(f"\n🎥 Video {idx+1}")
        print(f"Title: {video['title']}")
        print(f"Channel: {video['channel_title']}")
        print(f"Published: {video['publish_time']}")
        print(f"URL: {video['video_url']}")
        print(f"Description: {video['description'][:200]}...")  # Trimmed for readability


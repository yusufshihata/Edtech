import requests

# Get all topics
response = requests.get("https://www.khanacademy.org/api/v1/topics/")
topics = response

for topic in topics:
    print(topic)

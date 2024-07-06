import os
import json
from youtube_uploader_selenium import YouTubeUploader
from datetime import datetime, timedelta

def extractNumericPart(filename):
    return int(''.join(filter(str.isdigit, filename)))

def findHighestValueVideo(directory):
    videos = [f for f in os.listdir(directory) if f.endswith('.mp4')]
    if not videos:
        return None
    return max(videos, key=extractNumericPart)

outputDirectory = 'Output'
videoFilename = findHighestValueVideo(outputDirectory)

if videoFilename:
    videoPath = os.path.join(outputDirectory, videoFilename)
    videoNumber = extractNumericPart(videoFilename)
    metadataPath = os.path.join(outputDirectory, f'{videoNumber}/videoMetadata.json')

    metadata = {
        "title": f"Funny Random Memes #{videoNumber}",
        "description": f"Funny Random Memes #{videoNumber}",
        "tags": [
            "Gaming memes", "relatable memes", "funny memes", "relatable",
            "funny", "daily funny memes", "dank memes", "funny dank memes",
            "random memes", "latest memes", "memes shorts", "memes", "shorts",
            "american humor", "american people will relate", "American Memes",
            "USA Humor", "American Comedy", "USA Memes", "2manymemez",
            "Funny American Memes", "American Humor", "americans will relate"
        ],
        "schedule": (datetime.now() + timedelta(hours=2)).strftime("%m/%d/%Y, %H:%M")
    }

    with open(metadataPath, 'w') as metadataFile:
        json.dump(metadata, metadataFile, indent=2)

    uploader = YouTubeUploader(videoPath, metadataPath)
    wasVideoUploaded, videoId = uploader.upload()
    
    assert wasVideoUploaded
else:
    print("No videos found in the Output directory.")

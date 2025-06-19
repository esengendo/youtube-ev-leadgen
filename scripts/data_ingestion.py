"""
Data Ingestion Script for YouTube Comments
- Fetches all video IDs from given playlist(s)
- Fetches all comments (and replies) for each video
- Saves results as CSV in the local data/ directory
- Uses environment variables for API keys
"""
import os
import pandas as pd
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize YouTube API client
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_all_video_ids_from_playlists(youtube, playlist_ids):
    """
    Fetch all video IDs from a list of playlist IDs using the YouTube Data API.
    """
    all_videos = []
    for playlist_id in playlist_ids:
        next_page_token = None
        while True:
            playlist_request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            playlist_response = playlist_request.execute()
            all_videos.extend(
                item['contentDetails']['videoId'] for item in playlist_response['items']
            )
            next_page_token = playlist_response.get('nextPageToken')
            if not next_page_token:
                break
    return all_videos

def get_replies(youtube, parent_id, video_id):
    """
    Fetch all replies to a specific comment using the YouTube Data API.
    """
    replies = []
    next_page_token = None
    while True:
        reply_request = youtube.comments().list(
            part="snippet",
            parentId=parent_id,
            textFormat="plainText",
            maxResults=100,
            pageToken=next_page_token
        )
        reply_response = reply_request.execute()
        for item in reply_response['items']:
            comment = item['snippet']
            replies.append({
                'Timestamp': comment['publishedAt'],
                'Username': comment['authorDisplayName'],
                'VideoID': video_id,
                'Comment': comment['textDisplay'],
                'Date': comment.get('updatedAt', comment['publishedAt'])
            })
        next_page_token = reply_response.get('nextPageToken')
        if not next_page_token:
            break
    return replies

def get_comments_for_video(youtube, video_id):
    """
    Fetch all top-level comments and their replies for a given video.
    """
    all_comments = []
    next_page_token = None
    while True:
        comment_request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            pageToken=next_page_token,
            textFormat="plainText",
            maxResults=100
        )
        comment_response = comment_request.execute()
        for item in comment_response['items']:
            top_comment = item['snippet']['topLevelComment']['snippet']
            all_comments.append({
                'Timestamp': top_comment['publishedAt'],
                'Username': top_comment['authorDisplayName'],
                'VideoID': video_id,
                'Comment': top_comment['textDisplay'],
                'Date': top_comment.get('updatedAt', top_comment['publishedAt'])
            })
            if item['snippet']['totalReplyCount'] > 0:
                replies = get_replies(youtube, item['snippet']['topLevelComment']['id'], video_id)
                all_comments.extend(replies)
        next_page_token = comment_response.get('nextPageToken')
        if not next_page_token:
            break
    return all_comments

def main():
    # Replace with your playlist IDs
    playlist_ids = [
        'PLNcgB4fXotQFFQKtR51jUKnAMOr3k_dpP'
    ]
    video_ids = get_all_video_ids_from_playlists(youtube, playlist_ids)
    print(f"Found {len(video_ids)} videos.")
    all_comments = []
    for video_id in video_ids:
        print(f"Fetching comments for video: {video_id}")
        video_comments = get_comments_for_video(youtube, video_id)
        all_comments.extend(video_comments)
    comments_df = pd.DataFrame(all_comments)
    os.makedirs("data", exist_ok=True)
    csv_file = os.path.join("data", "comments_data.csv")
    comments_df.to_csv(csv_file, index=False)
    print(f"Saved all comments to {csv_file}")

if __name__ == "__main__":
    main()

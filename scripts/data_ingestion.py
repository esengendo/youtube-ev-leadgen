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
    try:
        logger.info("Starting YouTube data ingestion")
        
        # Replace with your playlist IDs
        playlist_ids = [
            'PLNcgB4fXotQFFQKtR51jUKnAMOr3k_dpP'
        ]
        
        video_ids = get_all_video_ids_from_playlists(youtube, playlist_ids)
        
        if not video_ids:
            logger.warning("No video IDs found")
            return False
        
        # Sample a subset if too many videos (for development/testing)
        max_videos = 100
        if len(video_ids) > max_videos:
            video_ids = video_ids[:max_videos]
            logger.info(f"Sampling first {max_videos} videos for processing")
        
        all_comments = []
        failed_videos = 0
        
        for i, video_id in enumerate(video_ids):
            logger.info(f"Processing video {i+1}/{len(video_ids)}: {video_id}")
            try:
                video_comments = get_comments_for_video(youtube, video_id)
                all_comments.extend(video_comments)
                logger.debug(f"Found {len(video_comments)} comments for video {video_id}")
                
                # Add delay between videos to respect rate limits
                if i < len(video_ids) - 1:
                    time.sleep(random.uniform(0.5, 1.5))
                    
            except Exception as e:
                logger.error(f"Error processing video {video_id}: {e}")
                failed_videos += 1
        
        # Save to CSV
        if all_comments:
            comments_df = pd.DataFrame(all_comments)
            file_paths = config_manager.get_file_paths()
            
            if data_loader.save_csv_safe(comments_df, file_paths['raw_comments']):
                logger.info(f"Successfully saved {len(all_comments)} comments")
                logger.info(f"Videos processed: {len(video_ids) - failed_videos}/{len(video_ids)}")
                return True
            else:
                logger.error("Failed to save comments data")
                return False
        else:
            logger.warning("No comments found!")
            return False
            
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        return False

if __name__ == "__main__":
    main()

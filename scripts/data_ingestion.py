"""
Data Ingestion Script for YouTube Comments
- Fetches all video IDs from given playlist(s)
- Fetches all comments (and replies) for each video
- Saves results as CSV in the local data/ directory
- Uses environment variables for API keys
"""
import os
import time
import random
import pandas as pd
from googleapiclient.discovery import build
from dotenv import load_dotenv
from logger_setup import get_logger
from utils import config_manager, data_loader
import concurrent.futures
from threading import Lock
import threading
from googleapiclient.errors import HttpError

# Get logger for this module
logger = get_logger(__name__)

# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Thread-safe rate limiting
rate_limiter_lock = Lock()
last_request_time = 0
min_request_interval = 0.1  # 100ms between requests

def create_youtube_client():
    """Create a YouTube API client - thread-safe"""
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def rate_limited_request(func, *args, **kwargs):
    """Execute API request with rate limiting and retry logic"""
    global last_request_time
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Rate limiting
            with rate_limiter_lock:
                now = time.time()
                time_since_last = now - last_request_time
                if time_since_last < min_request_interval:
                    time.sleep(min_request_interval - time_since_last)
                last_request_time = time.time()
            
            # Execute request
            return func(*args, **kwargs).execute()
            
        except HttpError as e:
            if e.resp.status == 403:  # Quota exceeded
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise e
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Request failed, retrying in {delay:.1f}s: {e}")
            time.sleep(delay)
    
    raise Exception(f"Failed after {max_retries} attempts")

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

def get_comments_for_video_optimized(youtube, video_id):
    """
    Optimized comment fetching with rate limiting and batch reply processing
    """
    all_comments = []
    reply_tasks = []  # Store reply fetching tasks
    next_page_token = None
    
    while True:
        try:
            comment_response = rate_limited_request(
                youtube.commentThreads().list,
                part="snippet",
                videoId=video_id,
                pageToken=next_page_token,
                textFormat="plainText",
                maxResults=100
            )
            
            for item in comment_response['items']:
                top_comment = item['snippet']['topLevelComment']['snippet']
                all_comments.append({
                    'Timestamp': top_comment['publishedAt'],
                    'Username': top_comment['authorDisplayName'],
                    'VideoID': video_id,
                    'Comment': top_comment['textDisplay'],
                    'Date': top_comment.get('updatedAt', top_comment['publishedAt'])
                })
                
                # Collect reply tasks for batch processing
                if item['snippet']['totalReplyCount'] > 0:
                    reply_tasks.append({
                        'parent_id': item['snippet']['topLevelComment']['id'],
                        'video_id': video_id
                    })
            
            next_page_token = comment_response.get('nextPageToken')
            if not next_page_token:
                break
                
        except Exception as e:
            logger.error(f"Error fetching comments for video {video_id}: {e}")
            break
    
    # Process replies with controlled concurrency
    if reply_tasks:
        logger.debug(f"Processing {len(reply_tasks)} reply threads for video {video_id}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            reply_futures = [
                executor.submit(get_replies_optimized, create_youtube_client(), task['parent_id'], task['video_id'])
                for task in reply_tasks
            ]
            
            for future in concurrent.futures.as_completed(reply_futures):
                try:
                    replies = future.result(timeout=30)
                    all_comments.extend(replies)
                except Exception as e:
                    logger.error(f"Error processing replies: {e}")
    
    return all_comments

def get_replies_optimized(youtube, parent_id, video_id):
    """
    Optimized reply fetching with rate limiting
    """
    replies = []
    next_page_token = None
    
    while True:
        try:
            reply_response = rate_limited_request(
                youtube.comments().list,
                part="snippet",
                parentId=parent_id,
                textFormat="plainText",
                maxResults=100,
                pageToken=next_page_token
            )
            
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
                
        except Exception as e:
            logger.error(f"Error fetching replies for parent {parent_id}: {e}")
            break
    
    return replies

def main():
    try:
        logger.info("Starting optimized YouTube data ingestion with concurrency")
        
        # Replace with your playlist IDs
        playlist_ids = [
            'PLNcgB4fXotQFFQKtR51jUKnAMOr3k_dpP'
        ]
        
        youtube_client = create_youtube_client()
        video_ids = get_all_video_ids_from_playlists(youtube_client, playlist_ids)
        
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
        
        # Process videos with controlled concurrency
        max_workers = 4  # Conservative concurrency to respect API limits
        logger.info(f"Processing {len(video_ids)} videos with {max_workers} concurrent workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit video processing tasks
            future_to_video = {
                executor.submit(process_video_safely, video_id, i+1, len(video_ids)): video_id 
                for i, video_id in enumerate(video_ids)
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_video):
                video_id = future_to_video[future]
                try:
                    video_comments = future.result(timeout=120)  # 2 minute timeout per video
                    if video_comments:
                        all_comments.extend(video_comments)
                        logger.debug(f"Collected {len(video_comments)} comments from video {video_id}")
                except Exception as e:
                    logger.error(f"Failed to process video {video_id}: {e}")
                    failed_videos += 1
        
        # Save to CSV
        if all_comments:
            comments_df = pd.DataFrame(all_comments)
            file_paths = config_manager.get_file_paths()
            raw_csv_path = file_paths['raw_comments']
            
            if data_loader.save_csv_safe(comments_df, raw_csv_path):
                logger.info(f"✅ Saved {len(all_comments)} comments to {raw_csv_path}")
                logger.info(f"📊 Success rate: {((len(video_ids) - failed_videos) / len(video_ids)) * 100:.1f}%")
                return True
            else:
                logger.error("Failed to save comments data")
                return False
        else:
            logger.warning("No comments collected")
            return False
            
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        return False

def process_video_safely(video_id, current_index, total_videos):
    """
    Safely process a single video with error handling and logging
    """
    logger.info(f"Processing video {current_index}/{total_videos}: {video_id}")
    try:
        youtube_client = create_youtube_client()
        video_comments = get_comments_for_video_optimized(youtube_client, video_id)
        logger.debug(f"Successfully processed video {video_id}: {len(video_comments)} comments")
        return video_comments
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {e}")
        return []

if __name__ == "__main__":
    main()

import re
import time
from datetime import datetime
import httpx
import asyncio
import os
import json
import csv
import sys
from typing import Dict, Any, List
from pathlib import Path

try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

sys.path.append('.')

@register_node
class XMediaDownloadNode(Node):
    """Node for downloading media from X (Twitter) posts"""
    NAME = "X Media Download"
    DESCRIPTION = "Download media files from X (Twitter) posts"
    CATEGORY = "Social Media"
    ICON = "download"
    
    INPUTS = {
        "cookie_file": {
            "label": "Cookie File",
            "description": "Path to the JSON file containing X (Twitter) cookies",
            "type": "STRING",
            "required": True
        },
        "user_name": {
            "label": "User Name",
            "description": "X (Twitter) username to download media from",
            "type": "STRING",
            "required": True
        },
        "max_tweets": {
            "label": "Max Tweets",
            "description": "Maximum number of tweets to process",
            "type": "INT",
            "required": False,
            "default": 10
        },
        "save_path": {
            "label": "Save Path",
            "description": "Directory path to save downloaded media",
            "type": "STRING",
            "required": True
        }
    }
    
    OUTPUTS = {
        "downloaded_files": {
            "label": "Downloaded Files",
            "description": "Dictionary of downloaded files organized by directory",
            "type": "DICT"
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the download operation was successful",
            "type": "BOOL"
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if download failed",
            "type": "STRING"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            # Get input parameters
            cookie_file = node_inputs.get("cookie_file")
            screen_name = node_inputs.get("user_name")
            max_tweets = int(node_inputs.get("max_tweets", 10))
            save_path = node_inputs.get("save_path")
            
            # Create save directory if it doesn't exist
            save_path = os.path.join(save_path, screen_name)
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            
            # Read cookie
            cookie_string, csrf_token = parse_cookie_json(cookie_file)
            if not cookie_string or not csrf_token:
                return {
                    "success": False,
                    "error_message": "Failed to parse cookie file",
                    "downloaded_files": {}
                }
            
            # Set request headers
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
                'cookie': cookie_string,
                'x-csrf-token': csrf_token
            }
            
            # Get user info
            user_info = User_info(screen_name)
            if not get_user_info(user_info, headers):
                return {
                    "success": False,
                    "error_message": "Failed to get user information",
                    "downloaded_files": {}
                }
            
            workflow_logger.info(f"Starting download for user @{screen_name}")
            workflow_logger.info(f"User info: {user_info.name} (@{user_info.screen_name})")
            
            # Start download
            await download_tweets(user_info, save_path, max_tweets, headers)
            
            # Get list of downloaded files organized by directory
            downloaded_files = {}
            for root, dirs, files in os.walk(save_path):
                rel_dir = os.path.relpath(root, save_path)
                if rel_dir == ".":
                    continue
                downloaded_files[rel_dir] = [f for f in files]
            
            workflow_logger.info(f"Download completed. Total directories: {len(downloaded_files)}")
            
            return {
                "success": True,
                "downloaded_files": downloaded_files,
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg,
                "downloaded_files": {}
            }

class User_info():
    def __init__(self, screen_name:str):
        self.screen_name = screen_name      #用户id( @后面的 )
        self.rest_id = None      #用户数字ID
        self.name = None         #用户昵称
        self.statuses_count = None #总推数(含转推)
        self.media_count = None  #含图片视频的推数(不含转推)

        self.save_path = None
        self.cursor = None       #下一页
        self.count = 0           #已获取计数,用于计算进度
        
        pass


def quote_url(url):
    return url.replace('{','%7B').replace('}','%7D')

def parse_cookie_json(json_file):
    """Parse cookie from JSON file and return cookie string and csrf token"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)
        
        # Extract auth_token and ct0 from cookies
        auth_token = None
        ct0 = None
        for cookie in cookie_data.get('cookies', []):
            if cookie.get('name') == 'auth_token':
                auth_token = cookie.get('value')
            elif cookie.get('name') == 'ct0':
                ct0 = cookie.get('value')
        
        if not auth_token or not ct0:
            return None, None
            
        return f"auth_token={auth_token}; ct0={ct0};", ct0
    except Exception:
        return None, None

def stamp2time(msecs_stamp:int) -> str:
    timeArray = time.localtime(msecs_stamp/1000)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M", timeArray)
    return otherStyleTime

class TweetCSV:
    def __init__(self, save_path: str, tweet_id: str, user_name: str, screen_name: str) -> None:
        # 为每条推文创建独立的文件夹
        self.tweet_folder = os.path.join(save_path, tweet_id)
        if not os.path.exists(self.tweet_folder):
            os.makedirs(self.tweet_folder)
            
        self.filename = f'{self.tweet_folder}/{tweet_id}.csv'
        self.f = open(self.filename, 'w', encoding='utf-8-sig', newline='')
        self.writer = csv.writer(self.f)
        
        # Write header
        self.writer.writerow([user_name, f'@{screen_name}'])
        self.writer.writerow(['Tweet ID', tweet_id])
        self.writer.writerow(['Tweet Date', 'Display Name', 'User Name', 'Tweet URL', 'Media Type', 'Media URL', 'Saved Filename', 'Tweet Content', 'Favorite Count', 
                            'Retweet Count', 'Reply Count'])

    def write_tweet(self, tweet_info: list):
        tweet_info[0] = stamp2time(tweet_info[0])  # Convert timestamp to readable format
        self.writer.writerow(tweet_info)

    def close(self):
        self.f.close()

def get_user_info(_user_info, _headers):
    url = 'https://twitter.com/i/api/graphql/xc8f1g7BYqr6VTzTbvNlGw/UserByScreenName?variables={"screen_name":"' + _user_info.screen_name + '","withSafetyModeUserFields":false}&features={"hidden_profile_likes_enabled":false,"hidden_profile_subscriptions_enabled":false,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}&fieldToggles={"withAuxiliaryUserLabels":false}'
    try:
        response = httpx.get(quote_url(url), headers=_headers).text
        raw_data = json.loads(response)
        _user_info.rest_id = raw_data['data']['user']['result']['rest_id']
        _user_info.name = raw_data['data']['user']['result']['legacy']['name']
        _user_info.statuses_count = raw_data['data']['user']['result']['legacy']['statuses_count']
        _user_info.media_count = raw_data['data']['user']['result']['legacy']['media_count']
    except Exception:
        return False
    return True

def print_info(_user_info):
    print(
        f'''
        <======基本信息=====>
        昵称:{_user_info.name}
        用户名:{_user_info.screen_name}
        数字ID:{_user_info.rest_id}
        总推数(含转推):{_user_info.statuses_count}
        含图片/视频/音频推数(不含转推):{_user_info.media_count}
        <==================>
        开始爬取...
        '''
    )

def get_heighest_video_quality(variants) -> str:
    if len(variants) == 1:      #gif适配
        return variants[0]['url']
    
    max_bitrate = 0
    heighest_url = None
    for i in variants:
        if 'bitrate' in i:
            if int(i['bitrate']) > max_bitrate:
                max_bitrate = int(i['bitrate'])
                heighest_url = i['url']
    return heighest_url

def sanitize_filename(filename: str) -> str:
    """Replace invalid characters in filename with underscores"""
    # Replace spaces, colons, slashes and other special characters with underscores
    invalid_chars = r'[<>:"/\\|?*\s]'  # Add \s to match all whitespace characters
    filename = re.sub(invalid_chars, '_', filename)
    # Replace consecutive underscores with a single underscore
    filename = re.sub(r'_+', '_', filename)
    # Remove leading and trailing underscores
    filename = filename.strip('_')
    return filename

async def download_media(url: str, save_path: str, filename: str, is_video: bool = False):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(quote_url(url), timeout=(3.05, 16))
            if response.status_code == 404:
                raise Exception('404')
            
            filename = sanitize_filename(filename)
            
            if is_video:
                filename = f'{filename}.mp4'
            else:
                filename = f'{filename}.jpg'
                
            full_path = os.path.join(save_path, filename)
            
            with open(full_path, 'wb') as f:
                f.write(response.content)
            return filename
    except Exception:
        return None

def generate_markdown(tweet_folder: str, tweet_data: dict, media_files: list):
    """生成类似Twitter风格的Markdown文件"""
    tweet_id = os.path.basename(tweet_folder)
    markdown_file = os.path.join(tweet_folder, f'{tweet_id}.md')
    
    with open(markdown_file, 'w', encoding='utf-8') as f:
        # 写入用户信息
        f.write(f"# {tweet_data['display_name']} (@{tweet_data['screen_name']})\n\n")
        
        # 写入推文内容
        f.write(f"{tweet_data['full_text']}\n\n")
        
        # 写入媒体内容
        if media_files:
            f.write("## Media\n\n")
            for media_file in media_files:
                # 使用相对路径
                relative_path = os.path.basename(media_file)
                if media_file.endswith('.jpg'):
                    f.write(f"![Image](./{relative_path})\n\n")
                elif media_file.endswith('.mp4'):
                    f.write(f"<video src=\"./{relative_path}\" controls></video>\n\n")
        
        # 写入互动数据
        f.write("## Engagement\n\n")
        f.write(f"- ❤️ {tweet_data['favorite_count']}\n")
        f.write(f"- 🔄 {tweet_data['retweet_count']}\n")
        f.write(f"- 💬 {tweet_data['reply_count']}\n\n")
        
        # 写入链接
        f.write(f"## Link\n\n")
        f.write(f"[View on Twitter](https://twitter.com/{tweet_data['screen_name']}/status/{tweet_id})\n")

async def get_self_replies(tweet_id: str, user_id: str, headers: dict) -> list:
    """获取自己的回复"""
    try:
        cursor = ''
        replies = []
        while True:
            variables = {
                "focalTweetId": tweet_id,
                "cursor": cursor,
                "with_rux_injections": False,
                "includePromotedContent": False,
                "withCommunity": True,
                "withQuickPromoteEligibilityTweetFields": False,
                "withBirdwatchNotes": False,
                "withVoice": True,
                "withV2Timeline": True
            }
            
            features = {
                "rweb_tipjar_consumption_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "creator_subscriptions_tweet_preview_api_enabled": True,
                "responsive_web_graphql_timeline_navigation_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "c9s_tweet_anatomy_moderator_badge_enabled": True,
                "articles_preview_enabled": True,
                "tweetypie_unmention_optimization_enabled": True,
                "responsive_web_edit_tweet_api_enabled": True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                "view_counts_everywhere_api_enabled": True,
                "longform_notetweets_consumption_enabled": True,
                "responsive_web_twitter_article_tweet_consumption_enabled": True,
                "tweet_awards_web_tipping_enabled": False,
                "creator_subscriptions_quote_tweet_preview_enabled": False,
                "freedom_of_speech_not_reach_fetch_enabled": True,
                "standardized_nudges_misinfo": True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                "tweet_with_visibility_results_prefer_gql_media_interstitial_enabled": True,
                "rweb_video_timestamps_enabled": True,
                "longform_notetweets_rich_text_read_enabled": True,
                "longform_notetweets_inline_media_enabled": True,
                "responsive_web_enhance_cards_enabled": False,
                "communities_web_enable_tweet_community_results_fetch": True
            }
            
            url = f'https://twitter.com/i/api/graphql/Ez6kRPyXbqNlhBwcNMpU-Q/TweetDetail?variables={json.dumps(variables)}&features={json.dumps(features)}'
            
            async with httpx.AsyncClient() as client:
                response = await client.get(quote_url(url), headers=headers)
                if response.status_code != 200:
                    break
                    
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    break
            
            if 'data' not in data or 'threaded_conversation_with_injections_v2' not in data['data']:
                break
                
            instructions = data['data']['threaded_conversation_with_injections_v2']['instructions']
            entries = instructions[0].get('entries', [])
            
            if not entries:
                break
                
            # 第一页第一条是父推文，跳过
            if not cursor:
                entries = entries[1:]
            
            # 检查是否有下一页
            if 'cursor-' not in entries[-1]['entryId']:
                is_last_page = True
            else:
                cursor = entries[-1]['content']['itemContent']['value']
                is_last_page = False
            
            # 处理回复
            for entry in entries:
                if 'conversationthread' in entry['entryId']:
                    reply = entry['content']['items'][0]
                    if 'conversationthread' not in reply['entryId']:
                        continue
                    reply_data = reply['item']['itemContent']['tweet_results']['result']
                    
                    # 只处理自己的回复
                    if reply_data['core']['user_results']['result']['rest_id'] == user_id:
                        replies.append(reply_data)
            
            if is_last_page:
                break
        
        return replies
    except Exception as e:
        print(f"获取回复失败: {e}")
        return []

async def process_tweet(tweet_data, user_info, save_path, semaphore, headers):
    try:
        if 'tweet' in tweet_data:
            tweet_data = tweet_data['tweet']
            
        tweet_id = tweet_data['legacy']['id_str']
        tweet_msecs = int(tweet_data['edit_control']['editable_until_msecs']) - 3600000
        display_name = tweet_data['core']['user_results']['result']['legacy']['name']
        screen_name = tweet_data['core']['user_results']['result']['legacy']['screen_name']
        
        # Create CSV file for this tweet
        csv_file = TweetCSV(save_path, tweet_id, display_name, screen_name)
        
        # Prepare tweet data for Markdown
        tweet_info = {
            'display_name': display_name,
            'screen_name': screen_name,
            'full_text': tweet_data['legacy']['full_text'],
            'favorite_count': tweet_data['legacy']['favorite_count'],
            'retweet_count': tweet_data['legacy']['retweet_count'],
            'reply_count': tweet_data['legacy']['reply_count']
        }
        
        # Process media if exists
        media_files = []
        if 'extended_entities' in tweet_data['legacy']:
            media_list = tweet_data['legacy']['extended_entities']['media']
            for media in media_list:
                media_type = 'Video' if 'video_info' in media else 'Image'
                media_url = get_heighest_video_quality(media['video_info']['variants']) if media_type == 'Video' else media['media_url_https']
                
                # Generate filename
                timestamp = stamp2time(tweet_msecs).replace(':', '-')
                filename = f'{timestamp}_{screen_name}_{tweet_id}'
                
                # Download media
                saved_filename = await download_media(media_url, csv_file.tweet_folder, filename, media_type == 'Video')
                
                if saved_filename:
                    media_files.append(saved_filename)
                
                # Prepare tweet info
                tweet_info_csv = [
                    tweet_msecs,
                    display_name,
                    f'@{screen_name}',
                    f'https://twitter.com/{screen_name}/status/{tweet_id}',
                    media_type,
                    media_url,
                    saved_filename or '',
                    tweet_data['legacy']['full_text'],
                    tweet_data['legacy']['favorite_count'],
                    tweet_data['legacy']['retweet_count'],
                    tweet_data['legacy']['reply_count']
                ]
                
                # Write to CSV
                csv_file.write_tweet(tweet_info_csv)
        
        # Get self replies
        self_replies = await get_self_replies(tweet_id, user_info.rest_id, headers)
        for reply in self_replies:
            reply_msecs = int(reply['edit_control']['editable_until_msecs']) - 3600000
            reply_text = reply['legacy']['full_text']
            
            # Process media in replies
            if 'extended_entities' in reply['legacy']:
                media_list = reply['legacy']['extended_entities']['media']
                for media in media_list:
                    media_type = 'Video' if 'video_info' in media else 'Image'
                    media_url = get_heighest_video_quality(media['video_info']['variants']) if media_type == 'Video' else media['media_url_https']
                    
                    # Generate filename
                    timestamp = stamp2time(reply_msecs).replace(':', '-')
                    filename = f'{timestamp}_{screen_name}_{reply["legacy"]["id_str"]}_reply'
                    
                    # Download media
                    saved_filename = await download_media(media_url, csv_file.tweet_folder, filename, media_type == 'Video')
                    
                    if saved_filename:
                        media_files.append(saved_filename)
                    
                    # Write reply to CSV
                    tweet_info_csv = [
                        reply_msecs,
                        display_name,
                        f'@{screen_name}',
                        f'https://twitter.com/{screen_name}/status/{reply["legacy"]["id_str"]}',
                        media_type,
                        media_url,
                        saved_filename or '',
                        reply_text,
                        reply['legacy']['favorite_count'],
                        reply['legacy']['retweet_count'],
                        reply['legacy']['reply_count']
                    ]
                    
                    csv_file.write_tweet(tweet_info_csv)
        
        csv_file.close()
        
        # Generate Markdown file
        generate_markdown(csv_file.tweet_folder, tweet_info, media_files)
        
        return True
    except Exception:
        return False

async def download_tweets(user_info, save_path, max_tweets, headers):
    semaphore = asyncio.Semaphore(8)  # Limit concurrent downloads
    cursor = ''
    processed_count = 0
    
    while processed_count < max_tweets:
        # Set required features
        features = {
            "rweb_tipjar_consumption_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "articles_preview_enabled": True,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": True,
            "tweet_awards_web_tipping_enabled": False,
            "creator_subscriptions_quote_tweet_preview_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "tweet_with_visibility_results_prefer_gql_media_interstitial_enabled": True,
            "rweb_video_timestamps_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_enhance_cards_enabled": False,
            "communities_web_enable_tweet_community_results_fetch": True
        }
        
        variables = {
            "userId": user_info.rest_id,
            "count": 20,
            "cursor": cursor,
            "includePromotedContent": False,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True
        }
        
        url = f'https://twitter.com/i/api/graphql/9zyyd1hebl7oNWIPdA8HRw/UserTweets?variables={json.dumps(variables)}&features={json.dumps(features)}'
        
        try:
            response = httpx.get(quote_url(url), headers=headers).text
            raw_data = json.loads(response)
            
            # Check for errors
            if 'errors' in raw_data or 'data' not in raw_data:
                break
                
            if 'user' not in raw_data['data'] or 'result' not in raw_data['data']['user']:
                break
                
            if 'timeline_v2' not in raw_data['data']['user']['result']:
                break
                
            if 'timeline' not in raw_data['data']['user']['result']['timeline_v2']:
                break
                
            if 'instructions' not in raw_data['data']['user']['result']['timeline_v2']['timeline']:
                break
                
            instructions = raw_data['data']['user']['result']['timeline_v2']['timeline']['instructions']
            if not instructions:
                break
                
            entries = instructions[-1].get('entries', [])
            if not entries or len(entries) <= 2:  # No more tweets
                break
                
            # Update cursor
            cursor = entries[-1]['content']['value']
            
            # Process tweets
            tasks = []
            for tweet in entries:
                if processed_count >= max_tweets:
                    break
                    
                if 'promoted-tweet' in tweet['entryId']:
                    continue
                if 'tweet' in tweet['entryId']:
                    tweet_data = tweet['content']['itemContent']['tweet_results']['result']
                    tasks.append(process_tweet(tweet_data, user_info, save_path, semaphore, headers))
                    processed_count += 1
            
            if tasks:
                await asyncio.gather(*tasks)
            
            # Exit if we've processed enough tweets
            if processed_count >= max_tweets:
                break
            
        except Exception:
            break

def main():
    # Set parameters
    screen_name = ""  # Username
    cookie_file = ""  # Cookie file path
    max_tweets = 10   # Maximum tweets to process
    
    # Create save directory
    save_path = os.path.join(os.getcwd(), screen_name)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    # Read cookie
    cookie_string, csrf_token = parse_cookie_json(cookie_file)
    if not cookie_string or not csrf_token:
        return
    
    # Set request headers
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'cookie': cookie_string,
        'x-csrf-token': csrf_token
    }
    
    # Get user info
    user_info = User_info(screen_name)
    if not get_user_info(user_info, headers):
        return
    
    # Start download
    asyncio.run(download_tweets(user_info, save_path, max_tweets, headers))

if __name__ == '__main__':
    main()

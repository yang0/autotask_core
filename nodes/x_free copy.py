import re
import time
from datetime import datetime
import httpx
import asyncio
import os
import json
import csv
import sys

sys.path.append('.')
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
            print("Error: Missing required cookies (auth_token or ct0) in JSON file")
            return None, None
            
        return f"auth_token={auth_token}; ct0={ct0};", ct0
    except Exception as e:
        print(f"Error reading cookie JSON file: {e}")
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
        print('获取信息失败')
        print(response)
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
    """替换文件名中的非法字符为下划线"""
    print(f"清理文件名前的原始文件名: {filename}")
    # 替换空格、冒号、斜杠等特殊字符为下划线
    invalid_chars = r'[<>:"/\\|?*\s]'  # 添加 \s 来匹配所有空白字符
    filename = re.sub(invalid_chars, '_', filename)
    print(f"替换非法字符后: {filename}")
    # 替换连续的下划线为单个下划线
    filename = re.sub(r'_+', '_', filename)
    print(f"替换连续下划线后: {filename}")
    # 移除开头和结尾的下划线
    filename = filename.strip('_')
    print(f"清理前后下划线后: {filename}")
    return filename

async def download_media(url: str, save_path: str, filename: str, is_video: bool = False):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(quote_url(url), timeout=(3.05, 16))
            if response.status_code == 404:
                raise Exception('404')
            
            print(f"\n开始处理媒体文件:")
            print(f"原始文件名: {filename}")
            # 先清理文件名
            filename = sanitize_filename(filename)
            print(f"清理后的文件名: {filename}")
            
            if is_video:
                filename = f'{filename}.mp4'
            else:
                filename = f'{filename}.jpg'
            print(f"添加扩展名后的最终文件名: {filename}")
                
            full_path = os.path.join(save_path, filename)
            print(f"完整文件路径: {full_path}")
            
            with open(full_path, 'wb') as f:
                f.write(response.content)
            return filename
    except Exception as e:
        print(f"下载失败: {url}")
        print(f"错误: {e}")
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

async def get_tweet_detail(tweet_id: str, headers: dict) -> dict:
    """获取推文详情"""
    try:
        variables = {
            "focalTweetId": tweet_id,
            "cursor": "",
            "referrer": "tweet",
            "with_rux_injections": False,
            "rankingMode": "Recency",
            "includePromotedContent": False,
            "withCommunity": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withBirdwatchNotes": True,
            "withVoice": True
        }
        
        features = {
            "profile_label_improvements_pcf_label_in_post_enabled": True,
            "rweb_tipjar_consumption_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "premium_content_api_read_enabled": False,
            "communities_web_enable_tweet_community_results_fetch": True,
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
            "responsive_web_grok_analyze_post_followups_enabled": True,
            "responsive_web_jetfuel_frame": False,
            "responsive_web_grok_share_attachment_enabled": True,
            "articles_preview_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": True,
            "tweet_awards_web_tipping_enabled": False,
            "responsive_web_grok_analysis_button_from_backend": False,
            "creator_subscriptions_quote_tweet_preview_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "rweb_video_timestamps_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_grok_image_annotation_enabled": True,
            "responsive_web_enhance_cards_enabled": False
        }
        
        url = f'https://twitter.com/i/api/graphql/Ez6kRPyXbqNlhBwcNMpU-Q/TweetDetail?variables={json.dumps(variables)}&features={json.dumps(features)}'
        
        print(f"\n获取推文 {tweet_id} 的详情...")
        async with httpx.AsyncClient() as client:
            response = await client.get(quote_url(url), headers=headers)
            if response.status_code != 200:
                print(f"API请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")  # 打印响应前200个字符
                return None
                
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                return None
        
        # 从详情页数据中提取完整文本
        if 'data' in data and 'threaded_conversation_with_injections_v2' in data['data']:
            instructions = data['data']['threaded_conversation_with_injections_v2']['instructions']
            for instruction in instructions:
                if 'entries' in instruction:
                    for entry in instruction['entries']:
                        if 'content' in entry and 'itemContent' in entry['content']:
                            tweet_result = entry['content']['itemContent'].get('tweet_results', {}).get('result', {})
                            if tweet_result.get('legacy', {}).get('id_str') == tweet_id:
                                return tweet_result
        
        print("未找到推文详情")
        return None
    except Exception as e:
        print(f"获取推文详情失败: {e}")
        return None

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
        
        print(f"\n处理推文 {tweet_id}:")
        print(f"显示名称: {display_name}")
        print(f"用户名: {screen_name}")
        
        # 获取推文详情
        tweet_detail = await get_tweet_detail(tweet_id, headers)
        if tweet_detail:
            tweet_data = tweet_detail
        
        # Create CSV file for this tweet
        csv_file = TweetCSV(save_path, tweet_id, display_name, screen_name)
        
        # 准备推文数据用于生成Markdown
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
        
        # 获取自己的回复
        self_replies = await get_self_replies(tweet_id, user_info.rest_id, headers)
        for reply in self_replies:
            reply_msecs = int(reply['edit_control']['editable_until_msecs']) - 3600000
            reply_text = reply['legacy']['full_text']
            
            # 处理回复中的媒体
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
        
        # 生成Markdown文件
        generate_markdown(csv_file.tweet_folder, tweet_info, media_files)
        
        return True
    except Exception as e:
        print(f"处理推文失败: {e}")
        return False

async def download_tweets(user_info, save_path, max_tweets, headers):
    semaphore = asyncio.Semaphore(8)  # 限制并发数
    cursor = ''
    processed_count = 0
    
    while processed_count < max_tweets:
        # 修改 features 参数，确保所有必需的特性都有值
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
            print(f"正在获取推文，cursor: {cursor}")
            response = httpx.get(quote_url(url), headers=headers).text
            print(f"API响应: {response[:200]}...")  # 打印响应前200个字符
            
            raw_data = json.loads(response)
            
            # 检查错误信息
            if 'errors' in raw_data:
                print(f"API返回错误: {raw_data['errors']}")
                break
                
            if 'data' not in raw_data:
                print(f"API响应中没有data字段: {raw_data}")
                break
                
            if 'user' not in raw_data['data']:
                print(f"API响应中没有user字段: {raw_data['data']}")
                break
                
            if 'result' not in raw_data['data']['user']:
                print(f"API响应中没有result字段: {raw_data['data']['user']}")
                break
                
            if 'timeline_v2' not in raw_data['data']['user']['result']:
                print(f"API响应中没有timeline_v2字段: {raw_data['data']['user']['result']}")
                break
                
            if 'timeline' not in raw_data['data']['user']['result']['timeline_v2']:
                print(f"API响应中没有timeline字段: {raw_data['data']['user']['result']['timeline_v2']}")
                break
                
            if 'instructions' not in raw_data['data']['user']['result']['timeline_v2']['timeline']:
                print(f"API响应中没有instructions字段: {raw_data['data']['user']['result']['timeline_v2']['timeline']}")
                break
                
            instructions = raw_data['data']['user']['result']['timeline_v2']['timeline']['instructions']
            if not instructions:
                print("API响应中instructions为空")
                break
                
            entries = instructions[-1].get('entries', [])
            if not entries:
                print("API响应中没有entries")
                break
                
            if len(entries) <= 2:  # No more tweets
                print("没有更多推文")
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
                results = await asyncio.gather(*tasks)
                success_count = sum(1 for r in results if r)
                print(f"已处理 {success_count}/{max_tweets} 条推文")
            
            # 如果已经处理完需要的推文数量，就退出循环
            if processed_count >= max_tweets:
                break
            
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"响应内容: {response[:500]}...")  # 打印响应前500个字符
            break
        except Exception as e:
            print(f"获取推文失败: {e}")
            print(f"响应内容: {response[:500]}...")  # 打印响应前500个字符
            break

def main():
    # 参数设置
    screen_name = "dotey"  # 用户名
    cookie_file = "g:/temp/cookies/x.com.json"  # cookie文件路径
    max_tweets = 10  # 最大推文数
    
    # 创建保存目录
    save_path = os.path.join(os.getcwd(), screen_name)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    # 读取cookie
    cookie_string, csrf_token = parse_cookie_json(cookie_file)
    if not cookie_string or not csrf_token:
        print("Failed to parse cookie file. Exiting...")
        return
    
    # 设置请求头
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'cookie': cookie_string,
        'x-csrf-token': csrf_token
    }
    
    # 获取用户信息
    user_info = User_info(screen_name)
    if not get_user_info(user_info, headers):
        return
    
    print_info(user_info)
    
    # 开始下载
    asyncio.run(download_tweets(user_info, save_path, max_tweets, headers))
    
    print(f"\n下载完成！共处理 {max_tweets} 条推文")

if __name__ == '__main__':
    main()

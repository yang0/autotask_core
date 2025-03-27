try:
    from autotask.nodes import Node, register_node
    from autotask.api_keys import get_api_key
    import tweepy
except ImportError:
    from stub import Node, register_node, get_api_key

from typing import Dict, Any, Optional
import json

# Get API keys at module level
BEARER_TOKEN = get_api_key(provider="browser_use", key_name="BEARER_TOKEN")
CONSUMER_KEY = get_api_key(provider="browser_use", key_name="CONSUMER_KEY")
CONSUMER_SECRET = get_api_key(provider="browser_use", key_name="CONSUMER_SECRET")
ACCESS_TOKEN = get_api_key(provider="browser_use", key_name="ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = get_api_key(provider="browser_use", key_name="ACCESS_TOKEN_SECRET")


def get_twitter_client() -> tweepy.Client:
    """Get Twitter API client with credentials from environment"""
    return tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )


@register_node
class XPostNode(Node):
    """Node for creating posts on X (Twitter)"""
    NAME = "X Post"
    DESCRIPTION = "Create a new post on X (Twitter)"
    CATEGORY = "Social Media"
    HELP_URL = "https://help.twitter.com/using-twitter/how-to-tweet"
    VERSION = "1.0.0"
    ICON = "🐦"
    
    INPUTS = {
        "text": {
            "label": "Post Text",
            "description": "The content of the post",
            "type": "STRING",
            "required": True,
            "placeholder": "Enter your tweet text here"
        }
    }
    
    OUTPUTS = {
        "post_url": {
            "label": "Post URL",
            "description": "URL of the created post",
            "type": "STRING"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            client = get_twitter_client()
            text = node_inputs["text"]
            workflow_logger.info(f"Creating X post: {text}")
            
            response = client.create_tweet(text=text)
            post_id = response.data["id"]
            user = client.get_me().data
            post_url = f"https://x.com/{user.username}/status/{post_id}"
            
            workflow_logger.info(f"Post created successfully: {post_url}")
            return {
                "success": True,
                "post_url": post_url
            }

        except Exception as e:
            workflow_logger.error(f"Post creation failed: {str(e)}")
            return {"success": False, "error_message": str(e)}


@register_node
class XReplyNode(Node):
    """Node for replying to posts on X (Twitter)"""
    NAME = "X Reply"
    DESCRIPTION = "Reply to an existing post on X (Twitter)"
    CATEGORY = "Social Media"
    HELP_URL = "https://help.twitter.com/using-twitter/mentions-and-replies"
    VERSION = "1.0.0"
    ICON = "↩️"
    
    INPUTS = {
        "post_id": {
            "label": "Post ID",
            "description": "The ID of the post to reply to",
            "type": "STRING",
            "required": True,
            "placeholder": "Enter the tweet ID to reply to"
        },
        "text": {
            "label": "Reply Text",
            "description": "The content of the reply",
            "type": "STRING",
            "required": True,
            "placeholder": "Enter your reply text here"
        }
    }
    
    OUTPUTS = {
        "reply_url": {
            "label": "Reply URL",
            "description": "URL of the reply post",
            "type": "STRING"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            client = get_twitter_client()
            post_id = node_inputs["post_id"]
            text = node_inputs["text"]
            workflow_logger.info(f"Replying to post {post_id} with: {text}")
            
            response = client.create_tweet(text=text, in_reply_to_tweet_id=post_id)
            reply_id = response.data["id"]
            user = client.get_me().data
            reply_url = f"https://x.com/{user.username}/status/{reply_id}"
            
            workflow_logger.info(f"Reply created successfully: {reply_url}")
            return {
                "success": True,
                "reply_url": reply_url
            }

        except Exception as e:
            workflow_logger.error(f"Reply creation failed: {str(e)}")
            return {"success": False, "error_message": str(e)}


@register_node
class XDirectMessageNode(Node):
    """Node for sending direct messages on X (Twitter)"""
    NAME = "X Direct Message"
    DESCRIPTION = "Send a direct message to a user on X (Twitter)"
    CATEGORY = "Social Media"
    HELP_URL = "https://help.twitter.com/using-twitter/direct-messages"
    VERSION = "1.0.0"
    ICON = "✉️"
    
    INPUTS = {
        "recipient": {
            "label": "Recipient",
            "description": "Username or user ID of the recipient",
            "type": "STRING",
            "required": True,
            "placeholder": "@username or user_id"
        },
        "text": {
            "label": "Message Text",
            "description": "The content of the direct message",
            "type": "STRING",
            "required": True,
            "placeholder": "Enter your message here"
        }
    }
    
    OUTPUTS = {
        "dm_id": {
            "label": "Message ID",
            "description": "ID of the sent direct message",
            "type": "STRING"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            client = get_twitter_client()
            recipient = node_inputs["recipient"]
            text = node_inputs["text"]
            
            # Check if recipient is a user ID (numeric) or username
            if not recipient.isdigit():
                user = client.get_user(username=recipient)
                recipient_id = user.data.id
            else:
                recipient_id = recipient

            workflow_logger.info(f"Sending DM to {recipient}")
            response = client.create_direct_message(participant_id=recipient_id, text=text)
            dm_id = response.data["id"]
            
            workflow_logger.info(f"DM sent successfully with ID: {dm_id}")
            return {
                "success": True,
                "dm_id": dm_id
            }

        except Exception as e:
            workflow_logger.error(f"DM sending failed: {str(e)}")
            return {"success": False, "error_message": str(e)}


@register_node
class XGetUserInfoNode(Node):
    """Node for retrieving user information from X (Twitter)"""
    NAME = "X Get User Info"
    DESCRIPTION = "Get information about a specific X user"
    CATEGORY = "Social Media"
    HELP_URL = "https://help.twitter.com/using-twitter/twitter-profiles"
    VERSION = "1.0.0"
    ICON = "👤"
    
    INPUTS = {
        "username": {
            "label": "Username",
            "description": "The username to get information about",
            "type": "STRING",
            "required": True,
            "placeholder": "@username"
        }
    }
    
    OUTPUTS = {
        "user_info": {
            "label": "User Information",
            "description": "Detailed information about the user",
            "type": "DICT"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            client = get_twitter_client()
            username = node_inputs["username"].strip("@")
            workflow_logger.info(f"Fetching information for user: {username}")
            
            user = client.get_user(
                username=username,
                user_fields=["description", "public_metrics", "created_at", "location", "verified"]
            )
            user_data = user.data.data
            
            user_info = {
                "id": user_data["id"],
                "name": user_data["name"],
                "username": user_data["username"],
                "description": user_data["description"],
                "followers_count": user_data["public_metrics"]["followers_count"],
                "following_count": user_data["public_metrics"]["following_count"],
                "tweet_count": user_data["public_metrics"]["tweet_count"],
                "created_at": user_data["created_at"].isoformat(),
                "location": user_data.get("location"),
                "verified": user_data.get("verified", False)
            }
            
            workflow_logger.info(f"Successfully retrieved user information for {username}")
            return {
                "success": True,
                "user_info": user_info
            }

        except Exception as e:
            workflow_logger.error(f"Failed to get user info: {str(e)}")
            return {"success": False, "error_message": str(e)}


@register_node
class XGetMyInfoNode(Node):
    """Node for retrieving authenticated user's information"""
    NAME = "X Get My Info"
    DESCRIPTION = "Get information about the authenticated user"
    CATEGORY = "Social Media"
    HELP_URL = "https://help.twitter.com/managing-your-account"
    VERSION = "1.0.0"
    ICON = "🪪"
    
    OUTPUTS = {
        "user_info": {
            "label": "User Information",
            "description": "Detailed information about the authenticated user",
            "type": "DICT"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            client = get_twitter_client()
            workflow_logger.info("Fetching authenticated user information")
            
            me = client.get_me(user_fields=["description", "public_metrics", "created_at", "location", "verified"])
            user_data = me.data.data
            
            user_info = {
                "id": user_data["id"],
                "name": user_data["name"],
                "username": user_data["username"],
                "description": user_data["description"],
                "followers_count": user_data["public_metrics"]["followers_count"],
                "following_count": user_data["public_metrics"]["following_count"],
                "tweet_count": user_data["public_metrics"]["tweet_count"],
                "created_at": user_data["created_at"].isoformat(),
                "location": user_data.get("location"),
                "verified": user_data.get("verified", False)
            }
            
            workflow_logger.info("Successfully retrieved authenticated user information")
            return {
                "success": True,
                "user_info": user_info
            }

        except Exception as e:
            workflow_logger.error(f"Failed to get authenticated user info: {str(e)}")
            return {"success": False, "error_message": str(e)}


@register_node
class XGetHomeTimelineNode(Node):
    """Node for retrieving home timeline tweets"""
    NAME = "X Get Home Timeline"
    DESCRIPTION = "Get recent tweets from your home timeline"
    CATEGORY = "Social Media"
    HELP_URL = "https://help.twitter.com/using-twitter/twitter-timeline"
    VERSION = "1.0.0"
    ICON = "🏠"
    
    INPUTS = {
        "max_results": {
            "label": "Maximum Results",
            "description": "Maximum number of tweets to retrieve (1-100)",
            "type": "INT",
            "required": True,
            "default": 10,
            "min": 1,
            "max": 100
        }
    }
    
    OUTPUTS = {
        "tweets": {
            "label": "Timeline Tweets",
            "description": "List of tweets from the home timeline",
            "type": "LIST"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            client = get_twitter_client()
            max_results = node_inputs.get("max_results", 10)
            workflow_logger.info(f"Fetching home timeline, max results: {max_results}")
            
            response = client.get_home_timeline(
                max_results=max_results,
                tweet_fields=["created_at", "public_metrics", "author_id"],
                expansions=["author_id"],
                user_fields=["username"]
            )
            
            tweets = []
            users = {user.id: user for user in response.includes["users"]} if "users" in response.includes else {}
            
            for tweet in response.data:
                author = users.get(tweet.author_id)
                tweet_data = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat(),
                    "author_id": tweet.author_id,
                    "author_username": author.username if author else None,
                    "metrics": tweet.public_metrics,
                    "url": f"https://x.com/{author.username if author else tweet.author_id}/status/{tweet.id}"
                }
                tweets.append(tweet_data)
            
            workflow_logger.info(f"Successfully retrieved {len(tweets)} tweets")
            return {
                "success": True,
                "tweets": tweets
            }

        except Exception as e:
            workflow_logger.error(f"Failed to get home timeline: {str(e)}")
            return {"success": False, "error_message": str(e)}

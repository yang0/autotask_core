try:
    from autotask.nodes import Node, register_node
    from youtube_transcript_api import YouTubeTranscriptApi
    import json
    from urllib.parse import parse_qs, urlencode, urlparse
    from urllib.request import urlopen
except ImportError:
    # Mock for development environment
    from ..stub import Node, register_node
    class YouTubeTranscriptApi:
        @staticmethod
        def get_transcript(video_id, **kwargs):
            return [{"text": "Mock transcript", "start": 0, "duration": 5}]

import asyncio
from typing import Dict, Any, List, Optional


@register_node
class YouTubeDataNode(Node):
    """Node for retrieving metadata about a YouTube video"""
    NAME = "YouTube Video Data"
    DESCRIPTION = "Retrieves metadata information from a YouTube video URL"
    CATEGORY = "Media"
    ICON = "youtube"
    
    INPUTS = {
        "url": {
            "label": "YouTube URL",
            "description": "The URL of the YouTube video",
            "type": "STRING",
            "required": True,
        }
    }
    
    OUTPUTS = {
        "video_data": {
            "label": "Video Data",
            "description": "JSON representation of the video metadata",
            "type": "STRING",
        },
        "video_id": {
            "label": "Video ID",
            "description": "The YouTube video ID",
            "type": "STRING",
        },
        "title": {
            "label": "Video Title",
            "description": "The title of the YouTube video",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if operation failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs.get("url", "")
            
            if not url:
                workflow_logger.error("No URL provided")
                return {
                    "success": "false",
                    "error_message": "No URL provided",
                    "video_data": "{}",
                    "video_id": "",
                    "title": ""
                }
            
            workflow_logger.info(f"Getting video data for YouTube video: {url}")
            
            # Extract video ID from URL
            video_id = self._get_youtube_video_id(url)
            if not video_id:
                workflow_logger.error("Invalid YouTube URL or could not extract video ID")
                return {
                    "success": "false",
                    "error_message": "Invalid YouTube URL or could not extract video ID",
                    "video_data": "{}",
                    "video_id": "",
                    "title": ""
                }
            
            # Get video metadata using YouTube oembed API
            params = {"format": "json", "url": f"https://www.youtube.com/watch?v={video_id}"}
            oembed_url = "https://www.youtube.com/oembed"
            query_string = urlencode(params)
            full_url = oembed_url + "?" + query_string
            
            with urlopen(full_url) as response:
                response_text = response.read()
                video_data = json.loads(response_text.decode())
                
                # Extract relevant data from the response
                clean_data = {
                    "title": video_data.get("title", ""),
                    "author_name": video_data.get("author_name", ""),
                    "author_url": video_data.get("author_url", ""),
                    "type": video_data.get("type", ""),
                    "height": video_data.get("height", 0),
                    "width": video_data.get("width", 0),
                    "version": video_data.get("version", ""),
                    "provider_name": video_data.get("provider_name", ""),
                    "provider_url": video_data.get("provider_url", ""),
                    "thumbnail_url": video_data.get("thumbnail_url", ""),
                    "video_id": video_id,
                    "video_url": url
                }
                
                workflow_logger.info(f"Successfully retrieved data for video: {clean_data.get('title', '')}")
                
                return {
                    "success": "true",
                    "video_data": json.dumps(clean_data, indent=2),
                    "video_id": video_id,
                    "title": clean_data.get("title", ""),
                    "error_message": ""
                }
            
        except Exception as e:
            error_msg = f"Error getting YouTube video data: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "video_data": "{}",
                "video_id": "",
                "title": ""
            }
    
    def _get_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract the video ID from a YouTube URL"""
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        
        if hostname == "youtu.be":
            return parsed_url.path[1:]
        
        if hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                query_params = parse_qs(parsed_url.query)
                return query_params.get("v", [None])[0]
            
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            
            if parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]
        
        return None


@register_node
class YouTubeCaptionsNode(Node):
    """Node for retrieving and processing captions from a YouTube video"""
    NAME = "YouTube Captions"
    DESCRIPTION = "Extracts and processes caption text from a YouTube video"
    CATEGORY = "Media"
    ICON = "closed-captioning"
    
    INPUTS = {
        "url": {
            "label": "YouTube URL",
            "description": "The URL of the YouTube video",
            "type": "STRING",
            "required": True,
        },
        "languages": {
            "label": "Preferred Languages",
            "description": "Comma-separated list of language codes (e.g., 'en,es') to prefer when retrieving captions",
            "type": "STRING",
            "default": "en",
            "required": False,
        },
        "format_as_text": {
            "label": "Format as Text",
            "description": "Whether to format captions as plain text instead of providing structured JSON data",
            "type": "STRING",
            "default": "true",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "captions": {
            "label": "Captions",
            "description": "Text content of the video captions",
            "type": "STRING",
        },
        "captions_json": {
            "label": "Captions JSON",
            "description": "Structured JSON representation of the captions including timestamps",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if operation failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs.get("url", "")
            languages_input = node_inputs.get("languages", "en")
            format_as_text_str = node_inputs.get("format_as_text", "true")
            
            # Parse languages input
            languages = [lang.strip() for lang in languages_input.split(",") if lang.strip()]
            
            # Parse format_as_text to boolean
            format_as_text = format_as_text_str.lower() == "true"
            
            if not url:
                workflow_logger.error("No URL provided")
                return {
                    "success": "false",
                    "error_message": "No URL provided",
                    "captions": "",
                    "captions_json": "[]"
                }
            
            workflow_logger.info(f"Getting captions for YouTube video: {url}")
            
            # Extract video ID from URL
            video_id = self._get_youtube_video_id(url)
            if not video_id:
                workflow_logger.error("Invalid YouTube URL or could not extract video ID")
                return {
                    "success": "false",
                    "error_message": "Invalid YouTube URL or could not extract video ID",
                    "captions": "",
                    "captions_json": "[]"
                }
            
            # Retrieve captions using YouTubeTranscriptApi
            try:
                transcript_options = {}
                if languages:
                    transcript_options["languages"] = languages
                
                captions = YouTubeTranscriptApi.get_transcript(video_id, **transcript_options)
                
                if not captions:
                    workflow_logger.warning(f"No captions found for video: {video_id}")
                    return {
                        "success": "true",
                        "error_message": "No captions found for this video",
                        "captions": "",
                        "captions_json": "[]"
                    }
                
                # Format captions as plain text if requested
                if format_as_text:
                    captions_text = " ".join(line["text"] for line in captions)
                else:
                    captions_text = ""
                
                workflow_logger.info(f"Successfully retrieved captions for video ID: {video_id}")
                
                return {
                    "success": "true",
                    "captions": captions_text,
                    "captions_json": json.dumps(captions, indent=2),
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error retrieving captions: {str(e)}"
                workflow_logger.error(error_msg)
                return {
                    "success": "false",
                    "error_message": error_msg,
                    "captions": "",
                    "captions_json": "[]"
                }
            
        except Exception as e:
            error_msg = f"Error processing YouTube captions: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "captions": "",
                "captions_json": "[]"
            }
    
    def _get_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract the video ID from a YouTube URL"""
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        
        if hostname == "youtu.be":
            return parsed_url.path[1:]
        
        if hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                query_params = parse_qs(parsed_url.query)
                return query_params.get("v", [None])[0]
            
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            
            if parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]
        
        return None


@register_node
class YouTubeTimestampsNode(Node):
    """Node for generating formatted timestamps from YouTube video captions"""
    NAME = "YouTube Timestamps"
    DESCRIPTION = "Generates formatted timestamps with captions from a YouTube video"
    CATEGORY = "Media"
    ICON = "clock"
    
    INPUTS = {
        "url": {
            "label": "YouTube URL",
            "description": "The URL of the YouTube video",
            "type": "STRING",
            "required": True,
        },
        "languages": {
            "label": "Preferred Languages",
            "description": "Comma-separated list of language codes (e.g., 'en,es') to prefer when retrieving captions",
            "type": "STRING",
            "default": "en",
            "required": False,
        },
        "format": {
            "label": "Timestamp Format",
            "description": "Format for timestamps: 'standard' (MM:SS) or 'detailed' (HH:MM:SS)",
            "type": "STRING",
            "default": "standard",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "timestamps": {
            "label": "Timestamps",
            "description": "Formatted timestamps with captions text",
            "type": "STRING",
        },
        "timestamps_json": {
            "label": "Timestamps JSON",
            "description": "Structured JSON representation of timestamps with captions",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if operation failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs.get("url", "")
            languages_input = node_inputs.get("languages", "en")
            format_type = node_inputs.get("format", "standard")
            
            # Parse languages input
            languages = [lang.strip() for lang in languages_input.split(",") if lang.strip()]
            
            if not url:
                workflow_logger.error("No URL provided")
                return {
                    "success": "false",
                    "error_message": "No URL provided",
                    "timestamps": "",
                    "timestamps_json": "[]"
                }
            
            workflow_logger.info(f"Generating timestamps for YouTube video: {url}")
            
            # Extract video ID from URL
            video_id = self._get_youtube_video_id(url)
            if not video_id:
                workflow_logger.error("Invalid YouTube URL or could not extract video ID")
                return {
                    "success": "false",
                    "error_message": "Invalid YouTube URL or could not extract video ID",
                    "timestamps": "",
                    "timestamps_json": "[]"
                }
            
            # Retrieve captions using YouTubeTranscriptApi
            try:
                transcript_options = {}
                if languages:
                    transcript_options["languages"] = languages
                
                captions = YouTubeTranscriptApi.get_transcript(video_id, **transcript_options)
                
                if not captions:
                    workflow_logger.warning(f"No captions found for video: {video_id}")
                    return {
                        "success": "true",
                        "error_message": "No captions found for this video",
                        "timestamps": "",
                        "timestamps_json": "[]"
                    }
                
                # Process captions into timestamps
                formatted_timestamps = []
                timestamps_data = []
                
                for item in captions:
                    start_time = item.get("start", 0)
                    text = item.get("text", "")
                    
                    # Format time based on format type
                    if format_type.lower() == "detailed":
                        hours, remainder = divmod(int(start_time), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:  # standard format
                        minutes, seconds = divmod(int(start_time), 60)
                        time_str = f"{minutes}:{seconds:02d}"
                    
                    formatted_timestamps.append(f"{time_str} - {text}")
                    
                    timestamps_data.append({
                        "time": time_str,
                        "start_seconds": start_time,
                        "text": text
                    })
                
                workflow_logger.info(f"Successfully generated timestamps for video ID: {video_id}")
                
                return {
                    "success": "true",
                    "timestamps": "\n".join(formatted_timestamps),
                    "timestamps_json": json.dumps(timestamps_data, indent=2),
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error generating timestamps: {str(e)}"
                workflow_logger.error(error_msg)
                return {
                    "success": "false",
                    "error_message": error_msg,
                    "timestamps": "",
                    "timestamps_json": "[]"
                }
            
        except Exception as e:
            error_msg = f"Error processing YouTube timestamps: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "timestamps": "",
                "timestamps_json": "[]"
            }
    
    def _get_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract the video ID from a YouTube URL"""
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        
        if hostname == "youtu.be":
            return parsed_url.path[1:]
        
        if hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                query_params = parse_qs(parsed_url.query)
                return query_params.get("v", [None])[0]
            
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            
            if parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]
        
        return None


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test video URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Test YouTubeDataNode
    print("\nTesting YouTubeDataNode:")
    data_node = YouTubeDataNode()
    result = asyncio.run(data_node.execute({"url": test_url}, logger))
    print(f"Success: {result['success']}")
    print(f"Video ID: {result['video_id']}")
    print(f"Title: {result['title']}")
    
    # Test YouTubeCaptionsNode
    print("\nTesting YouTubeCaptionsNode:")
    captions_node = YouTubeCaptionsNode()
    result = asyncio.run(captions_node.execute({"url": test_url, "format_as_text": "true"}, logger))
    print(f"Success: {result['success']}")
    caption_preview = result['captions'][:100] + "..." if len(result['captions']) > 100 else result['captions']
    print(f"Captions preview: {caption_preview}")
    
    # Test YouTubeTimestampsNode
    print("\nTesting YouTubeTimestampsNode:")
    timestamps_node = YouTubeTimestampsNode()
    result = asyncio.run(timestamps_node.execute({"url": test_url, "format": "standard"}, logger))
    print(f"Success: {result['success']}")
    timestamps_preview = result['timestamps'].split("\n")[:3]
    print(f"Timestamps preview (first 3 lines):")
    for line in timestamps_preview:
        print(f"  {line}") 
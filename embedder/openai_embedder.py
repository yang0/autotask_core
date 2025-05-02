from autotask.embedder.base_embedder import BaseEmbedder
from autotask.embedder.embedder_registry import EmbedderRegistry
from typing import Dict, List, Optional, Tuple

@EmbedderRegistry.register_embedder
class OpenAIEmbedder(BaseEmbedder):
    """OpenAI嵌入模型实现"""
    
    company = "OpenAI"
    model_name = "text-embedding-ada-002"
    dimensions = 1536
    doc_url = "https://platform.openai.com/docs/guides/embeddings"
    api_url = "https://api.openai.com/v1/embeddings"
    
    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
    
    def get_embedding_and_usage(self, text: str) -> Tuple[List[float], Optional[Dict]]:
        if not self.api_key:
            raise ValueError("API密钥未设置，请提供api_key参数")
        # lazy import requests/json
        import requests
        import json
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "input": text,
            "model": self.model_name
        }
        response = requests.post(
            self.api_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=self.timeout
        )
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code} {response.text}")
        data = response.json()
        embedding = data["data"][0]["embedding"]
        usage = data.get("usage", {})
        return embedding, usage
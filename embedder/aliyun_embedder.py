from autotask.embedder.base_embedder import BaseEmbedder
from autotask.embedder.embedder_registry import EmbedderRegistry
import os
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import traceback

@EmbedderRegistry.register_embedder
class AliyunEmbedder(BaseEmbedder):
    """阿里云文本嵌入模型实现"""
    
    company = "Aliyun"
    model_name = "text-embedding-v3"
    dimensions = 1024  # 默认维度，可根据需要调整
    doc_url = "https://help.aliyun.com/zh/model-studio/user-guide/embedding"
    api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        # 是否指定维度
        if "dimensions" in kwargs:
            self.dimensions = kwargs["dimensions"]
    
    def get_embedding_and_usage(self, text: str) -> Tuple[List[float], Optional[Dict]]:
        """获取文本嵌入向量和使用情况"""
        if not self.api_key:
            raise ValueError("API密钥未设置，请提供api_key参数或设置DASHSCOPE_API_KEY环境变量")
        
        # 创建OpenAI客户端，使用阿里云兼容端点
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )
        
        try:
            response = client.embeddings.create(
                model=self.model_name,
                input=text,
                dimensions=self.dimensions,
                encoding_format="float"
            )
            
            # 获取嵌入向量
            embedding = response.data[0].embedding
            
            # 提取使用情况
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return embedding, usage
            
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"阿里云API请求失败: {str(e)}")
    
    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量获取文本嵌入向量"""
        if not self.api_key:
            raise ValueError("API密钥未设置，请提供api_key参数或设置DASHSCOPE_API_KEY环境变量")
        
        # 创建OpenAI客户端，使用阿里云兼容端点
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )
        
        try:
            response = client.embeddings.create(
                model=self.model_name,
                input=texts,
                dimensions=self.dimensions,
                encoding_format="float"
            )
            
            # 获取所有嵌入向量
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as e:
            raise Exception(f"阿里云API批量请求失败: {str(e)}")
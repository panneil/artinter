"""
多种LLM提供商支持模块
支持云服务、Web服务和本地模型
"""

import os
import json
import requests
import subprocess
import threading
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """LLM提供商基类"""
    
    @abstractmethod
    def generate_text(self, prompt, options=None):
        """生成文本"""
        pass
        
    @abstractmethod
    def generate_image(self, prompt, options=None):
        """生成图像"""
        pass
    
    @abstractmethod
    def verify_connection(self):
        """验证连接"""
        pass

# 云服务提供商 ===========================================

class OpenAIProvider(LLMProvider):
    """OpenAI API服务"""
    
    def __init__(self, api_key=None, model="gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
        
    def generate_text(self, prompt, options=None):
        """使用OpenAI生成文本"""
        if not self.api_key:
            return {"error": "需要API密钥"}
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if options:
            data.update(options)
            
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions", 
                headers=headers, 
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
            
    def generate_image(self, prompt, options=None):
        """使用DALL-E生成图像"""
        if not self.api_key:
            return {"error": "需要API密钥"}
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }
        
        if options:
            data.update(options)
            
        try:
            response = requests.post(
                f"{self.base_url}/images/generations",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
            
    def verify_connection(self):
        """验证OpenAI API连接"""
        if not self.api_key:
            return {"status": "error", "message": "缺少API密钥"}
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers
            )
            response.raise_for_status()
            return {"status": "success", "message": "连接成功", "models": response.json()}
        except Exception as e:
            return {"status": "error", "message": f"连接失败: {str(e)}"}


class GeminiProvider(LLMProvider):
    """Google Gemini API服务"""
    
    def __init__(self, api_key=None, model="gemini-pro"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    def generate_text(self, prompt, options=None):
        """使用Gemini生成文本"""
        if not self.api_key:
            return {"error": "需要API密钥"}
            
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        if options:
            data.update(options)
            
        try:
            response = requests.post(
                f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
            
    def generate_image(self, prompt, options=None):
        """Gemini目前不支持图像生成"""
        return {"error": "Gemini不支持图像生成"}
            
    def verify_connection(self):
        """验证Gemini API连接"""
        if not self.api_key:
            return {"status": "error", "message": "缺少API密钥"}
            
        try:
            # 简单测试生成
            response = self.generate_text("Hello")
            if "error" in response:
                return {"status": "error", "message": f"连接失败: {response['error']}"}
            return {"status": "success", "message": "连接成功"}
        except Exception as e:
            return {"status": "error", "message": f"连接失败: {str(e)}"}


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API服务"""
    
    def __init__(self, api_key=None, model="claude-3-opus-20240229"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
        
    def generate_text(self, prompt, options=None):
        """使用Claude生成文本"""
        if not self.api_key:
            return {"error": "需要API密钥"}
            
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024
        }
        
        if options:
            data.update(options)
            
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
            
    def generate_image(self, prompt, options=None):
        """Claude不支持图像生成"""
        return {"error": "Claude不支持图像生成"}
            
    def verify_connection(self):
        """验证Claude API连接"""
        if not self.api_key:
            return {"status": "error", "message": "缺少API密钥"}
            
        try:
            # 简单测试生成
            response = self.generate_text("Hello")
            if "error" in response:
                return {"status": "error", "message": f"连接失败: {response['error']}"}
            return {"status": "success", "message": "连接成功"}
        except Exception as e:
            return {"status": "error", "message": f"连接失败: {str(e)}"}

# 网页服务集成 ===========================================

class WebServiceProvider(LLMProvider):
    """网页服务集成基类"""
    
    def __init__(self, service_url, auth_token=None):
        self.service_url = service_url
        self.auth_token = auth_token
        
    def generate_text(self, prompt, options=None):
        """抽象方法"""
        pass
        
    def generate_image(self, prompt, options=None):
        """抽象方法"""
        pass
        
    def verify_connection(self):
        """抽象方法"""
        pass


class PerplexityProvider(WebServiceProvider):
    """Perplexity AI服务集成"""
    
    def __init__(self, api_key=None, model="sonar-small-online"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.perplexity.ai"
        
    def generate_text(self, prompt, options=None):
        """使用Perplexity生成文本"""
        if not self.api_key:
            return {"error": "需要API密钥"}
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if options:
            data.update(options)
            
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
            
    def generate_image(self, prompt, options=None):
        """Perplexity不支持图像生成"""
        return {"error": "Perplexity不支持图像生成"}
            
    def verify_connection(self):
        """验证Perplexity API连接"""
        if not self.api_key:
            return {"status": "error", "message": "缺少API密钥"}
            
        try:
            response = self.generate_text("Hello")
            if "error" in response:
                return {"status": "error", "message": f"连接失败: {response['error']}"}
            return {"status": "success", "message": "连接成功"}
        except Exception as e:
            return {"status": "error", "message": f"连接失败: {str(e)}"}

# 本地模型支持 ===========================================

class OllamaProvider(LLMProvider):
    """本地Ollama模型支持"""
    
    def __init__(self, model="llama3", host="http://localhost:11434"):
        self.model = model
        self.host = host
        
    def generate_text(self, prompt, options=None):
        """使用Ollama生成文本"""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if options:
            data.update(options)
            
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
            
    def generate_image(self, prompt, options=None):
        """Ollama目前不支持图像生成"""
        return {"error": "Ollama不支持图像生成"}
            
    def verify_connection(self):
        """验证Ollama连接"""
        try:
            response = requests.get(f"{self.host}/api/tags")
            response.raise_for_status()
            return {"status": "success", "message": "连接成功", "models": response.json()}
        except Exception as e:
            return {"status": "error", "message": f"连接失败: {str(e)}"}


class LMStudioProvider(LLMProvider):
    """本地LM Studio模型支持"""
    
    def __init__(self, host="http://localhost:1234"):
        self.host = host
        
    def generate_text(self, prompt, options=None):
        """使用LM Studio生成文本"""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 512
        }
        
        if options:
            data.update(options)
            
        try:
            response = requests.post(
                f"{self.host}/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
            
    def generate_image(self, prompt, options=None):
        """LM Studio不支持图像生成"""
        return {"error": "LM Studio不支持图像生成"}
            
    def verify_connection(self):
        """验证LM Studio连接"""
        try:
            response = requests.get(f"{self.host}/v1/models")
            response.raise_for_status()
            return {"status": "success", "message": "连接成功", "data": response.json()}
        except Exception as e:
            return {"status": "error", "message": f"连接失败: {str(e)}"}

# 工厂类 =================================================

class LLMProviderFactory:
    """LLM提供商工厂类"""
    
    @staticmethod
    def create_provider(provider_type, config=None):
        """创建提供商实例"""
        if not config:
            config = {}
            
        if provider_type == "openai":
            return OpenAIProvider(
                api_key=config.get("api_key"),
                model=config.get("model", "gpt-4o")
            )
        elif provider_type == "gemini":
            return GeminiProvider(
                api_key=config.get("api_key"),
                model=config.get("model", "gemini-pro")
            )
        elif provider_type == "anthropic":
            return AnthropicProvider(
                api_key=config.get("api_key"),
                model=config.get("model", "claude-3-opus-20240229")
            )
        elif provider_type == "perplexity":
            return PerplexityProvider(
                api_key=config.get("api_key"),
                model=config.get("model", "sonar-small-online")
            )
        elif provider_type == "ollama":
            return OllamaProvider(
                model=config.get("model", "llama3"),
                host=config.get("host", "http://localhost:11434")
            )
        elif provider_type == "lmstudio":
            return LMStudioProvider(
                host=config.get("host", "http://localhost:1234")
            )
        else:
            raise ValueError(f"不支持的提供商类型: {provider_type}") 
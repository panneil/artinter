import requests

class SilijiClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn"  # 硅基流动的API地址
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(self, messages, **kwargs):
        """调用硅基流动的chat completion API"""
        endpoint = "/v1/chat/completions"
        
        # 默认参数
        payload = {
            "model": "deepseek-ai/DeepSeek-V3",
            "messages": messages,
            "stream": False,
            "max_tokens": 512,
            "stop": ["null"],
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "response_format": {"type": "text"},
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "description": "<string>",
                        "name": "<string>",
                        "parameters": {},
                        "strict": False
                    }
                }
            ]
        }
        
        # 更新用户提供的参数
        payload.update(kwargs)
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=payload,
            stream=kwargs.get('stream', False)  # 设置流模式
        )
        
        # 如果是流式响应，返回原始响应对象
        if kwargs.get('stream', False):
            return response
        else:
            # 否则返回JSON解析后的结果
            return response.json()
    
    def get_model_list(self):
        """获取可用模型列表"""
        endpoint = "/v1/models"
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers
        )
        return response.json()
    
    def get_account_info(self):
        """获取账户信息"""
        endpoint = "/v1/account/info"
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers
        )
        return response.json()
    
    def get_market_data(self, symbol):
        """获取市场数据"""
        endpoint = f"/v1/market/data/{symbol}"  # 根据实际API路径调整
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers
        )
        return response.json() 
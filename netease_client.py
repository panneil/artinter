import requests
import json
import base64
import hashlib
import time
import hmac
import uuid

class NeteaseClient:
    """网易云API客户端"""
    
    def __init__(self, api_key, secret_key):
        """初始化网易云客户端
        
        Args:
            api_key: 网易云API密钥
            secret_key: 网易云Secret密钥
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://yidun.163.com/api"
    
    def _generate_signature(self, params, secret_key):
        """生成网易云接口签名
        
        Args:
            params: 请求参数
            secret_key: 密钥
            
        Returns:
            str: 签名字符串
        """
        # 按照字典排序
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # 拼接请求参数
        param_str = ""
        for key, value in sorted_params:
            param_str += f"{key}{value}"
            
        # 生成签名
        signature = hashlib.md5((secret_key + param_str + secret_key).encode('utf-8')).hexdigest()
        
        return signature
    
    def ocr_general(self, image_path):
        """通用文字识别
        
        Args:
            image_path: 图像文件路径或URL
            
        Returns:
            str: 识别出的文本
        """
        endpoint = "/ocr/recognize"
        
        # 构建请求参数
        params = {
            "appId": self.api_key,
            "timestamp": str(int(time.time() * 1000)),
            "nonce": str(uuid.uuid4()).replace("-", "")
        }
        
        # 读取图像文件
        if image_path.startswith(('http://', 'https://')):
            # 如果是URL，将URL添加到参数中
            params["url"] = image_path
        else:
            # 如果是本地文件，读取并编码
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
                params["image"] = image_base64
        
        # 生成签名
        signature = self._generate_signature(params, self.secret_key)
        params["signature"] = signature
        
        # 发送请求
        response = requests.post(
            f"{self.base_url}{endpoint}",
            data=params
        )
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"OCR请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if result.get("code") != 200:
            raise Exception(f"OCR识别错误: {result.get('msg', '未知错误')}")
        
        # 提取文本
        text_lines = []
        if "result" in result and "texts" in result["result"]:
            for item in result["result"]["texts"]:
                text_lines.append(item.get("content", ""))
            
        return "\n".join(text_lines) if text_lines else "未识别到文本"
    
    def image_recognition(self, image_path):
        """图像识别
        
        Args:
            image_path: 图像文件路径或URL
            
        Returns:
            list: 识别结果列表
        """
        endpoint = "/image/recognition"
        
        # 构建请求参数
        params = {
            "appId": self.api_key,
            "timestamp": str(int(time.time() * 1000)),
            "nonce": str(uuid.uuid4()).replace("-", "")
        }
        
        # 读取图像文件
        if image_path.startswith(('http://', 'https://')):
            # 如果是URL，将URL添加到参数中
            params["url"] = image_path
        else:
            # 如果是本地文件，读取并编码
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
                params["image"] = image_base64
        
        # 生成签名
        signature = self._generate_signature(params, self.secret_key)
        params["signature"] = signature
        
        # 发送请求
        response = requests.post(
            f"{self.base_url}{endpoint}",
            data=params
        )
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"图像识别请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if result.get("code") != 200:
            raise Exception(f"图像识别错误: {result.get('msg', '未知错误')}")
        
        # 提取识别结果
        recognition_results = []
        if "result" in result and "tags" in result["result"]:
            for tag in result["result"]["tags"]:
                recognition_results.append({
                    "keyword": tag.get("name", "未知"),
                    "score": tag.get("confidence", 0)
                })
            
        return recognition_results
    
    def speech_recognition(self, audio_file):
        """语音识别
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            str: 识别结果文本
        """
        endpoint = "/smartasr/recognize"
        
        # 构建请求参数
        params = {
            "appId": self.api_key,
            "timestamp": str(int(time.time() * 1000)),
            "nonce": str(uuid.uuid4()).replace("-", "")
        }
        
        # 读取音频文件
        with open(audio_file, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode('utf-8')
            params["audio"] = audio_base64
        
        # 生成签名
        signature = self._generate_signature(params, self.secret_key)
        params["signature"] = signature
        
        # 发送请求
        response = requests.post(
            f"{self.base_url}{endpoint}",
            data=params
        )
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"语音识别请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if result.get("code") != 200:
            raise Exception(f"语音识别错误: {result.get('msg', '未知错误')}")
        
        # 提取识别结果
        recognition_text = ""
        if "result" in result and "text" in result["result"]:
            recognition_text = result["result"]["text"]
            
        return recognition_text 
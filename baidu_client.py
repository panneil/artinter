import requests
import json
import base64
import hmac
import hashlib
import time
import urllib.parse
import os
from urllib.parse import urlencode

class BaiduClient:
    """百度云API客户端"""
    
    def __init__(self, api_key, secret_key):
        """初始化百度云客户端
        
        Args:
            api_key: 百度云API密钥
            secret_key: 百度云Secret密钥
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.access_token = None
        self.token_expiry = 0
        
    def get_access_token(self):
        """获取百度云访问令牌
        
        Returns:
            str: 访问令牌
        """
        # 检查令牌是否已过期
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token
        
        # 获取新令牌
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        response = requests.post(url, params=params)
        result = response.json()
        
        if "access_token" not in result:
            raise Exception(f"获取访问令牌失败: {result.get('error_description', '未知错误')}")
        
        self.access_token = result["access_token"]
        # 设置过期时间（提前5分钟过期以确保安全）
        self.token_expiry = time.time() + result.get("expires_in", 2592000) - 300
        
        return self.access_token
    
    def ocr_general(self, image_path):
        """通用文字识别
        
        Args:
            image_path: 图像文件路径或URL
            
        Returns:
            str: 识别出的文本
        """
        token = self.get_access_token()
        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={token}"
        
        # 读取图像文件
        if image_path.startswith(('http://', 'https://')):
            # 如果是URL，直接使用URL识别
            params = {"url": image_path}
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            response = requests.post(url, data=params, headers=headers)
        else:
            # 如果是本地文件，读取并编码
            with open(image_path, "rb") as f:
                image = base64.b64encode(f.read())
            
            params = {"image": image}
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            response = requests.post(url, data=params, headers=headers)
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"OCR请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if "error_code" in result:
            raise Exception(f"OCR识别错误: {result['error_msg']}")
        
        # 提取文本
        words = []
        for item in result.get("words_result", []):
            words.append(item.get("words", ""))
        
        return "\n".join(words)
    
    def ocr_file(self, file_path, url_param=False):
        """通过文件路径或URL进行OCR识别
        
        Args:
            file_path: 文件路径或URL
            url_param: 是否是URL，默认为False
            
        Returns:
            识别结果文本
        """
        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={self.get_access_token()}"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        if url_param:
            # 使用URL进行识别
            payload = {
                'url': file_path,
                'detect_direction': 'false',
                'paragraph': 'false',
                'probability': 'false'
            }
        else:
            # 使用文件进行识别
            with open(file_path, 'rb') as f:
                image_data = base64.b64encode(f.read())
            
            payload = {
                'image': image_data,
                'detect_direction': 'false',
                'paragraph': 'false',
                'probability': 'false'
            }
        
        response = requests.post(url, data=payload, headers=headers)
        result = response.json()
        
        if "error_code" in result:
            error_msg = result.get("error_msg", "未知错误")
            raise Exception(f"OCR识别失败: {error_msg}")
        
        # 提取文本内容
        if "words_result" in result:
            return "\n".join([item["words"] for item in result["words_result"]])
        else:
            return "未识别到文本"
    
    def image_recognition(self, image_path):
        """图像识别
        
        Args:
            image_path: 图像文件路径或URL
            
        Returns:
            list: 识别结果列表
        """
        token = self.get_access_token()
        url = f"https://aip.baidubce.com/rest/2.0/image-classify/v2/advanced_general?access_token={token}"
        
        # 读取图像文件
        if image_path.startswith(('http://', 'https://')):
            # 如果是URL，直接使用URL识别
            params = {"url": image_path}
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            response = requests.post(url, data=params, headers=headers)
        else:
            # 如果是本地文件，读取并编码
            with open(image_path, "rb") as f:
                image = base64.b64encode(f.read())
            
            params = {"image": image}
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            response = requests.post(url, data=params, headers=headers)
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"图像识别请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if "error_code" in result:
            raise Exception(f"图像识别错误: {result['error_msg']}")
        
        return result.get("result", [])
    
    def translate(self, text, from_lang="zh", to_lang="en"):
        """文本翻译
        
        Args:
            text: 要翻译的文本
            from_lang: 源语言，默认中文
            to_lang: 目标语言，默认英文
            
        Returns:
            str: 翻译结果
        """
        token = self.get_access_token()
        url = f"https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1?access_token={token}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "q": text,
            "from": from_lang,
            "to": to_lang
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"翻译请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if "error_code" in result:
            raise Exception(f"翻译错误: {result['error_msg']}")
        
        # 提取翻译结果
        trans_result = result.get("result", {}).get("trans_result", [])
        translations = []
        for item in trans_result:
            translations.append(item.get("dst", ""))
        
        return "\n".join(translations)
    
    def nlp_lexer(self, text):
        """中文分词
        
        Args:
            text: 要分析的文本
            
        Returns:
            dict: 分词结果
        """
        token = self.get_access_token()
        url = f"https://aip.baidubce.com/rpc/2.0/nlp/v1/lexer?access_token={token}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {"text": text}
        
        response = requests.post(url, json=payload, headers=headers)
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"分词请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if "error_code" in result:
            raise Exception(f"分词错误: {result['error_msg']}")
        
        return result
    
    def speech_recognition(self, audio_file):
        """语音识别
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            str: 识别结果文本
        """
        token = self.get_access_token()
        url = f"https://vop.baidu.com/server_api?access_token={token}"
        
        # 读取音频文件
        with open(audio_file, 'rb') as f:
            speech_data = f.read()
        
        file_len = len(speech_data)
        file_format = os.path.splitext(audio_file)[1][1:].lower()  # 获取文件扩展名
        
        # 确定格式
        if file_format == 'wav':
            format_str = 'wav'
            rate = 16000  # 采样率默认16K
        elif file_format == 'pcm':
            format_str = 'pcm'
            rate = 16000
        elif file_format in ['mp3', 'amr', 'm4a']:
            format_str = file_format
            rate = 16000
        else:
            # 默认按照wav处理
            format_str = 'wav'
            rate = 16000
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        params = {
            "format": format_str,
            "rate": rate,
            "channel": 1,  # 单声道
            "cuid": "siliji_app",  # 用户标识
            "token": token,
            "dev_pid": 1537,  # 中文普通话(有标点)
            "speech": base64.b64encode(speech_data).decode('utf-8'),
            "len": file_len
        }
        
        response = requests.post(url, json=params, headers=headers)
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"语音识别请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if result.get("err_no") != 0:
            raise Exception(f"语音识别错误: {result.get('err_msg', '未知错误')}")
        
        # 提取识别结果
        return result.get("result", [""])[0] 
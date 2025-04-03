import requests
import json
import base64
import hmac
import hashlib
import uuid
import time
from datetime import datetime
import urllib.parse
from urllib.parse import urlencode
import hmac
import hashlib
import base64


class AliyunClient:
    """阿里云API客户端"""
    
    def __init__(self, api_key, secret_key):
        """初始化阿里云客户端
        
        Args:
            api_key: 阿里云AccessKey ID
            secret_key: 阿里云AccessKey Secret
        """
        self.access_key = api_key
        self.access_secret = secret_key
        self.ocr_url = "https://ocr.cn-shanghai.aliyuncs.com"
        self.image_url = "https://imagerecog.cn-shanghai.aliyuncs.com"
        self.asr_url = "https://nls-meta.cn-shanghai.aliyuncs.com"
        
    def _generate_signature(self, params, method, content_type=None):
        """生成阿里云API签名
        
        Args:
            params: 请求参数
            method: HTTP方法
            content_type: 内容类型
            
        Returns:
            dict: 包含签名的请求头
        """
        # 当前时间
        now = datetime.datetime.utcnow()
        date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 规范化请求
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        canonicalized_query_string = "&".join([
            f"{urllib.parse.quote(k)}={urllib.parse.quote(str(v))}"
            for k, v in sorted_params
        ])
        
        # 构建待签名字符串
        string_to_sign = f"{method}&%2F&{urllib.parse.quote(canonicalized_query_string)}"
        
        # 计算签名
        hmac_key = self.access_secret + "&"
        signature = base64.b64encode(
            hmac.new(
                hmac_key.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                hashlib.sha1
            ).digest()
        ).decode("utf-8")
        
        # 构建认证头
        auth_params = {
            "AccessKeyId": self.access_key,
            "Signature": signature,
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "SignatureNonce": str(uuid.uuid4()),
            "Timestamp": date,
            "Version": "2019-08-15",  # 使用最新版API版本
            "Format": "JSON"
        }
        
        # 合并参数
        params.update(auth_params)
        
        # 构建请求头
        headers = {
            "Accept": "application/json",
            "x-acs-signature-nonce": auth_params["SignatureNonce"],
            "x-acs-signature-method": "HMAC-SHA1",
            "x-acs-signature-version": "1.0",
            "x-acs-version": "2019-08-15",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AliyunClient/1.0.0"
        }
        
        if content_type:
            headers["Content-Type"] = content_type
            
        return headers, params
        
    def ocr_general(self, image_path):
        """通用文字识别
        
        Args:
            image_path: 图像文件路径或URL
            
        Returns:
            str: 识别出的文本
        """
        endpoint = "/ocr/general"
        
        # 基本请求参数
        params = {
            "Action": "RecognizeGeneral",
            "RegionId": "cn-shanghai"
        }
        
        # 读取图像数据
        if image_path.startswith(('http://', 'https://')):
            params["ImageURL"] = image_path
            body = None
        else:
            # 本地文件，读取内容
            with open(image_path, "rb") as f:
                image_data = f.read()
                body = base64.b64encode(image_data).decode("utf-8")
                params["ImageContent"] = body
        
        # 生成签名和请求头
        headers, signed_params = self._generate_signature(
            params, 
            "POST", 
            "application/x-www-form-urlencoded"
        )
        
        # 发送请求
        response = requests.post(
            f"{self.ocr_url}{endpoint}",
            data=signed_params,
            headers=headers
        )
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"OCR请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if "Data" not in result:
            raise Exception(f"OCR识别错误: {result.get('Message', '未知错误')}")
        
        # 提取文本
        text_blocks = []
        if "Blocks" in result["Data"]:
            for block in result["Data"]["Blocks"]:
                if "Text" in block:
                    text_blocks.append(block["Text"])
        
        return "\n".join(text_blocks) if text_blocks else "未识别到文本"
        
    def image_recognition(self, image_path):
        """图像识别
        
        Args:
            image_path: 图像文件路径或URL
            
        Returns:
            list: 识别结果列表
        """
        endpoint = "/image/tag"
        
        # 基本请求参数
        params = {
            "Action": "TaggingImage",
            "RegionId": "cn-shanghai"
        }
        
        # 读取图像数据
        if image_path.startswith(('http://', 'https://')):
            params["ImageURL"] = image_path
            body = None
        else:
            # 本地文件，读取内容
            with open(image_path, "rb") as f:
                image_data = f.read()
                body = base64.b64encode(image_data).decode("utf-8")
                params["ImageContent"] = body
        
        # 生成签名和请求头
        headers, signed_params = self._generate_signature(
            params, 
            "POST", 
            "application/x-www-form-urlencoded"
        )
        
        # 发送请求
        response = requests.post(
            f"{self.image_url}{endpoint}",
            data=signed_params,
            headers=headers
        )
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"图像识别请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if "Data" not in result:
            raise Exception(f"图像识别错误: {result.get('Message', '未知错误')}")
        
        # 提取结果
        recognition_results = []
        if "Tags" in result["Data"]:
            for tag in result["Data"]["Tags"]:
                recognition_results.append({
                    "keyword": tag.get("Value", "未知"),
                    "score": float(tag.get("Confidence", 0)) / 100
                })
        
        return recognition_results
    
    def speech_recognition(self, audio_file):
        """语音识别
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            str: 识别结果文本
        """
        # 获取口令
        token = self._get_token()
        if not token:
            raise Exception("无法获取语音识别服务口令")
        
        # 语音识别服务地址
        asr_url = "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/asr"
        
        # 读取音频文件
        with open(audio_file, "rb") as f:
            audio_content = f.read()
        
        # 请求头
        headers = {
            "Content-Type": "application/octet-stream",
            "X-NLS-Token": token,
            "Content-Length": str(len(audio_content)),
            "Accept": "application/json"
        }
        
        # 请求参数
        params = {
            "format": "wav",
            "sample_rate": 16000,
            "enable_punctuation": True,
            "enable_inverse_text_normalization": True
        }
        
        # 将参数添加到URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{asr_url}?{query_string}"
        
        # 发送请求
        response = requests.post(
            url,
            data=audio_content,
            headers=headers
        )
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"语音识别请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if result.get("status") != 20000000:
            raise Exception(f"语音识别错误: {result.get('message', '未知错误')}")
        
        # 提取识别结果
        return result.get("result", "")
    
    def _get_token(self):
        """获取阿里云NLS服务的访问令牌
        
        Returns:
            str: 访问令牌
        """
        # 获取Token的API地址
        token_url = "https://nls-meta.cn-shanghai.aliyuncs.com/pop/2018-05-18/tokens"
        
        # 请求参数
        params = {}
        
        # 请求体
        body = {
            "Action": "CreateToken",
            "Version": "2018-05-18",
            "AccessKeyId": self.access_key,
            "AccessKeySecret": self.access_secret
        }
        
        # 生成签名和请求头
        headers, _ = self._generate_signature(
            params, 
            "POST", 
            "application/json"
        )
        
        # 发送请求
        response = requests.post(
            token_url,
            json=body,
            headers=headers
        )
        
        # 处理结果
        if response.status_code != 200:
            return None
        
        result = response.json()
        if "Token" not in result:
            return None
            
        return result["Token"].get("Id") 
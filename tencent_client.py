import requests
import json
import base64
import hmac
import hashlib
import time
import random
import string

class TencentClient:
    """腾讯云API客户端"""
    
    def __init__(self, api_key, secret_key):
        """初始化腾讯云客户端
        
        Args:
            api_key: 腾讯云SecretId
            secret_key: 腾讯云SecretKey
        """
        self.secret_id = api_key
        self.secret_key = secret_key
        self.base_url = "https://ocr.tencentcloudapi.com"
        self.image_base_url = "https://tiia.tencentcloudapi.com"
        self.asr_base_url = "https://asr.tencentcloudapi.com"
        
    def _generate_signature(self, params, service, endpoint, payload):
        """生成腾讯云API请求签名
        
        Args:
            params: 请求参数
            service: 服务名称
            endpoint: 接口名称
            payload: 请求体
            
        Returns:
            dict: 包含签名的请求头
        """
        # 时间戳
        timestamp = int(time.time())
        date = time.strftime("%Y-%m-%d", time.localtime(timestamp))
        
        # 组装规范请求串
        canonical_uri = "/"
        canonical_querystring = ""
        ct = "application/json; charset=utf-8"
        payload = json.dumps(payload)
        canonical_headers = "content-type:" + ct + "\nhost:" + params["host"] + "\n"
        signed_headers = "content-type;host"
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = params["method"] + "\n" + canonical_uri + "\n" + canonical_querystring + "\n" + canonical_headers + "\n" + signed_headers + "\n" + hashed_request_payload
        
        # 组装签名串
        algorithm = "TC3-HMAC-SHA256"
        credential_scope = date + "/" + service + "/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = algorithm + "\n" + str(timestamp) + "\n" + credential_scope + "\n" + hashed_canonical_request
        
        # 计算签名
        def sign(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
            
        secret_date = sign(("TC3" + self.secret_key).encode("utf-8"), date)
        secret_service = sign(secret_date, service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        
        # 组装授权信息
        authorization = (
            algorithm + " " +
            "Credential=" + self.secret_id + "/" + credential_scope + ", " +
            "SignedHeaders=" + signed_headers + ", " +
            "Signature=" + signature
        )
        
        # 返回请求头
        headers = {
            "Authorization": authorization,
            "Content-Type": ct,
            "Host": params["host"],
            "X-TC-Action": endpoint,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": params["version"],
            "X-TC-Region": params.get("region", "ap-guangzhou")
        }
        
        if "token" in params:
            headers["X-TC-Token"] = params["token"]
            
        return headers
        
    def ocr_general(self, image_path):
        """通用文字识别
        
        Args:
            image_path: 图像文件路径或URL
            
        Returns:
            str: 识别出的文本
        """
        endpoint = "GeneralBasicOCR"
        service = "ocr"
        
        # 请求参数
        params = {
            "method": "POST",
            "host": "ocr.tencentcloudapi.com",
            "version": "2018-11-19",
            "region": "ap-guangzhou"
        }
        
        # 读取图像文件
        if image_path.startswith(('http://', 'https://')):
            # 如果是URL，使用URL参数
            payload = {"ImageUrl": image_path}
        else:
            # 如果是本地文件，读取并编码
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
                payload = {"ImageBase64": image_base64}
        
        # 生成签名和请求头
        headers = self._generate_signature(params, service, endpoint, payload)
        
        # 发送请求
        response = requests.post(
            f"{self.base_url}",
            headers=headers,
            data=json.dumps(payload)
        )
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"OCR请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if "Response" not in result:
            raise Exception(f"OCR识别错误: {result.get('Error', {}).get('Message', '未知错误')}")
        
        # 提取文本
        text_lines = []
        if "TextDetections" in result["Response"]:
            for item in result["Response"]["TextDetections"]:
                text_lines.append(item.get("DetectedText", ""))
        
        return "\n".join(text_lines) if text_lines else "未识别到文本"
        
    def image_recognition(self, image_path):
        """图像识别
        
        Args:
            image_path: 图像文件路径或URL
            
        Returns:
            list: 识别结果列表
        """
        endpoint = "DetectLabel"
        service = "tiia"
        
        # 请求参数
        params = {
            "method": "POST",
            "host": "tiia.tencentcloudapi.com",
            "version": "2019-05-29",
            "region": "ap-guangzhou"
        }
        
        # 读取图像文件
        if image_path.startswith(('http://', 'https://')):
            # 如果是URL，使用URL参数
            payload = {"ImageUrl": image_path}
        else:
            # 如果是本地文件，读取并编码
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
                payload = {"ImageBase64": image_base64}
        
        # 生成签名和请求头
        headers = self._generate_signature(params, service, endpoint, payload)
        
        # 发送请求
        response = requests.post(
            f"{self.image_base_url}",
            headers=headers,
            data=json.dumps(payload)
        )
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"图像识别请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if "Response" not in result:
            raise Exception(f"图像识别错误: {result.get('Error', {}).get('Message', '未知错误')}")
        
        # 提取识别结果
        recognition_results = []
        if "Labels" in result["Response"]:
            for label in result["Response"]["Labels"]:
                recognition_results.append({
                    "keyword": label.get("Name", "未知"),
                    "score": label.get("Confidence", 0) / 100
                })
        
        return recognition_results
    
    def speech_recognition(self, audio_file):
        """语音识别
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            str: 识别结果文本
        """
        endpoint = "CreateRecTask"
        service = "asr"
        
        # 请求参数
        params = {
            "method": "POST",
            "host": "asr.tencentcloudapi.com",
            "version": "2019-06-14",
            "region": "ap-guangzhou"
        }
        
        # 读取音频文件
        with open(audio_file, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # 构建请求体
        payload = {
            "EngineModelType": "16k_zh",
            "ChannelNum": 1,
            "ResTextFormat": 0,
            "SourceType": 1,
            "Data": audio_base64
        }
        
        # 生成签名和请求头
        headers = self._generate_signature(params, service, endpoint, payload)
        
        # 发送请求
        response = requests.post(
            f"{self.asr_base_url}",
            headers=headers,
            data=json.dumps(payload)
        )
        
        # 处理结果
        if response.status_code != 200:
            raise Exception(f"语音识别请求失败: HTTP {response.status_code}")
        
        result = response.json()
        if "Response" not in result:
            raise Exception(f"语音识别错误: {result.get('Error', {}).get('Message', '未知错误')}")
        
        # 获取任务ID
        task_id = result["Response"].get("Data", {}).get("TaskId")
        if not task_id:
            raise Exception("无法获取语音识别任务ID")
        
        # 等待任务完成
        for _ in range(10):  # 最多等待10次
            time.sleep(2)  # 等待2秒
            
            # 查询任务状态
            endpoint = "DescribeTaskStatus"
            payload = {"TaskId": task_id}
            headers = self._generate_signature(params, service, endpoint, payload)
            
            # 发送查询请求
            query_response = requests.post(
                f"{self.asr_base_url}",
                headers=headers,
                data=json.dumps(payload)
            )
            
            if query_response.status_code != 200:
                continue
                
            query_result = query_response.json()
            if "Response" not in query_result:
                continue
                
            # 检查任务是否完成
            status = query_result["Response"].get("Data", {}).get("Status")
            if status == 2:  # 任务成功
                return query_result["Response"]["Data"].get("Result", "")
            elif status == 3:  # 任务失败
                raise Exception("语音识别任务失败")
        
        raise Exception("语音识别任务超时") 
"""
网络协议提供商模块
支持WebDAV文件管理
"""

import os
import io
import base64
import requests
from urllib.parse import urlparse, unquote
import xml.etree.ElementTree as ET
from datetime import datetime

class WebDAVClient:
    """WebDAV客户端类"""
    
    def __init__(self, server_url, username=None, password=None):
        """初始化WebDAV客户端"""
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
            
    def verify_connection(self):
        """验证WebDAV连接"""
        try:
            response = self.session.request(
                'PROPFIND',
                self.server_url,
                headers={'Depth': '0'},
                verify=False
            )
            
            if response.status_code in (207, 200):
                return {"status": "success", "message": "连接成功"}
            else:
                return {"status": "error", "message": f"连接失败: HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"连接失败: {str(e)}"}
            
    def list_files(self, path='/'):
        """列出文件和目录"""
        url = f"{self.server_url}{path}"
        
        try:
            response = self.session.request(
                'PROPFIND',
                url,
                headers={'Depth': '1'},
                verify=False
            )
            
            if response.status_code != 207:
                return {"error": f"列出文件失败: HTTP {response.status_code}"}
                
            # 解析XML响应
            root = ET.fromstring(response.content)
            
            # 定义命名空间
            ns = {
                'd': 'DAV:',
            }
            
            items = []
            
            # 跳过第一个（当前目录）
            for response_tag in root.findall('.//d:response', ns)[1:]:
                href = response_tag.find('./d:href', ns).text
                
                # 解析文件名
                path_parts = urlparse(href).path.split('/')
                name = unquote(path_parts[-2] if href.endswith('/') else path_parts[-1])
                
                # 解析类型和大小
                prop_stat = response_tag.find('./d:propstat/d:prop', ns)
                
                # 判断是否为目录
                is_dir = prop_stat.find('./d:resourcetype/d:collection', ns) is not None
                
                # 获取大小
                size_tag = prop_stat.find('./d:getcontentlength', ns)
                size = int(size_tag.text) if size_tag is not None and size_tag.text else 0
                
                # 获取修改时间
                mtime_tag = prop_stat.find('./d:getlastmodified', ns)
                mtime = mtime_tag.text if mtime_tag is not None else None
                
                items.append({
                    'name': name,
                    'path': href,
                    'is_dir': is_dir,
                    'size': size,
                    'mtime': mtime
                })
                
            return {
                "path": path,
                "items": items
            }
        except Exception as e:
            return {"error": str(e)}
            
    def download_file(self, path):
        """下载文件"""
        url = f"{self.server_url}{path}"
        
        try:
            response = self.session.get(url, verify=False)
            
            if response.status_code != 200:
                return {"error": f"下载文件失败: HTTP {response.status_code}"}
                
            # 返回文件内容
            return {
                "content": response.content,
                "content_type": response.headers.get('Content-Type', 'application/octet-stream')
            }
        except Exception as e:
            return {"error": str(e)}
            
    def upload_file(self, path, content):
        """上传文件"""
        url = f"{self.server_url}{path}"
        
        try:
            response = self.session.put(url, data=content, verify=False)
            
            if response.status_code not in (201, 204):
                return {"error": f"上传文件失败: HTTP {response.status_code}"}
                
            return {"status": "success", "message": "文件上传成功"}
        except Exception as e:
            return {"error": str(e)}
            
    def delete_file(self, path):
        """删除文件或目录"""
        url = f"{self.server_url}{path}"
        
        try:
            response = self.session.delete(url, verify=False)
            
            if response.status_code not in (204, 200):
                return {"error": f"删除失败: HTTP {response.status_code}"}
                
            return {"status": "success", "message": "删除成功"}
        except Exception as e:
            return {"error": str(e)}
            
    def create_directory(self, path):
        """创建目录"""
        url = f"{self.server_url}{path}"
        
        try:
            response = self.session.request('MKCOL', url, verify=False)
            
            if response.status_code not in (201, 200):
                return {"error": f"创建目录失败: HTTP {response.status_code}"}
                
            return {"status": "success", "message": "目录创建成功"}
        except Exception as e:
            return {"error": str(e)}
            
    def copy_file(self, source_path, dest_path):
        """复制文件或目录"""
        source_url = f"{self.server_url}{source_path}"
        dest_url = f"{self.server_url}{dest_path}"
        
        try:
            response = self.session.request(
                'COPY',
                source_url,
                headers={'Destination': dest_url},
                verify=False
            )
            
            if response.status_code not in (201, 204):
                return {"error": f"复制失败: HTTP {response.status_code}"}
                
            return {"status": "success", "message": "复制成功"}
        except Exception as e:
            return {"error": str(e)}
            
    def move_file(self, source_path, dest_path):
        """移动文件或目录"""
        source_url = f"{self.server_url}{source_path}"
        dest_url = f"{self.server_url}{dest_path}"
        
        try:
            response = self.session.request(
                'MOVE',
                source_url,
                headers={'Destination': dest_url},
                verify=False
            )
            
            if response.status_code not in (201, 204):
                return {"error": f"移动失败: HTTP {response.status_code}"}
                
            return {"status": "success", "message": "移动成功"}
        except Exception as e:
            return {"error": str(e)}
            
    def backup_data(self, local_dir, remote_dir, file_patterns=None):
        """备份数据到WebDAV"""
        if not os.path.exists(local_dir):
            return {"error": f"本地目录不存在: {local_dir}"}
            
        # 创建远程目录
        create_result = self.create_directory(remote_dir)
        if "error" in create_result:
            # 忽略目录已存在的错误
            pass
            
        # 默认备份所有文件
        if file_patterns is None:
            file_patterns = ["*"]
            
        # 获取要备份的文件列表
        import glob
        files_to_backup = []
        for pattern in file_patterns:
            pattern_path = os.path.join(local_dir, pattern)
            files_to_backup.extend(glob.glob(pattern_path))
            
        results = {
            "success": [],
            "failed": []
        }
        
        # 上传文件
        for file_path in files_to_backup:
            if os.path.isfile(file_path):
                # 计算相对路径
                rel_path = os.path.relpath(file_path, local_dir)
                remote_path = f"{remote_dir}/{rel_path}"
                
                try:
                    # 读取文件内容
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        
                    # 上传文件
                    upload_result = self.upload_file(remote_path, content)
                    
                    if "error" in upload_result:
                        results["failed"].append({
                            "file": file_path,
                            "error": upload_result["error"]
                        })
                    else:
                        results["success"].append(file_path)
                except Exception as e:
                    results["failed"].append({
                        "file": file_path,
                        "error": str(e)
                    })
                    
        return results


class NetworkManager:
    """网络管理器类"""
    
    def __init__(self):
        """初始化网络管理器"""
        self.webdav_clients = {}
        
    def add_webdav_client(self, name, server_url, username=None, password=None):
        """添加WebDAV客户端"""
        client = WebDAVClient(server_url, username, password)
        self.webdav_clients[name] = client
        return client
        
    def get_webdav_client(self, name):
        """获取WebDAV客户端"""
        return self.webdav_clients.get(name) 
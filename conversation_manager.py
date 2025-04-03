"""
对话管理器模块
支持多模型同时对话
"""

import os
import json
import uuid
import time
from datetime import datetime

class Message:
    """消息类"""
    
    def __init__(self, content, role="user", timestamp=None, message_id=None):
        self.id = message_id or str(uuid.uuid4())
        self.content = content
        self.role = role  # user, assistant, system
        self.timestamp = timestamp or datetime.now().isoformat()
        
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp
        }
        
    @classmethod
    def from_dict(cls, data):
        """从字典创建消息"""
        return cls(
            content=data.get("content", ""),
            role=data.get("role", "user"),
            timestamp=data.get("timestamp"),
            message_id=data.get("id")
        )


class Conversation:
    """对话类"""
    
    def __init__(self, title=None, assistant_id=None, conversation_id=None):
        self.id = conversation_id or str(uuid.uuid4())
        self.title = title or f"对话 {time.strftime('%Y-%m-%d %H:%M')}"
        self.assistant_id = assistant_id
        self.messages = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
    def add_message(self, content, role="user"):
        """添加消息"""
        message = Message(content, role)
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()
        return message
        
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "assistant_id": self.assistant_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
    @classmethod
    def from_dict(cls, data):
        """从字典创建对话"""
        conversation = cls(
            title=data.get("title"),
            assistant_id=data.get("assistant_id"),
            conversation_id=data.get("id")
        )
        conversation.created_at = data.get("created_at", conversation.created_at)
        conversation.updated_at = data.get("updated_at", conversation.updated_at)
        
        # 加载消息
        messages_data = data.get("messages", [])
        conversation.messages = [Message.from_dict(msg) for msg in messages_data]
        
        return conversation
        
    def get_messages_for_api(self, include_system=True):
        """获取用于API调用的消息格式"""
        messages = []
        
        # 系统消息只添加一次
        if include_system:
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            if system_messages:
                messages.append({"role": "system", "content": system_messages[-1].content})
        
        # 添加用户和助手消息
        for msg in self.messages:
            if msg.role != "system":
                messages.append({"role": msg.role, "content": msg.content})
                
        return messages


class ConversationManager:
    """对话管理器类"""
    
    def __init__(self, config_dir):
        """初始化对话管理器"""
        self.config_dir = config_dir
        self.conversations_dir = os.path.join(config_dir, "conversations")
        self.conversations = {}
        self.current_conversation_id = None
        
        # 创建对话目录
        if not os.path.exists(self.conversations_dir):
            os.makedirs(self.conversations_dir)
            
        # 加载对话
        self.load_conversations()
        
    def load_conversations(self):
        """加载所有对话"""
        for filename in os.listdir(self.conversations_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.conversations_dir, filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        conversation = Conversation.from_dict(data)
                        self.conversations[conversation.id] = conversation
                except Exception as e:
                    print(f"加载对话失败 {filename}: {e}")
                    
    def save_conversation(self, conversation):
        """保存对话"""
        # 更新时间戳
        conversation.updated_at = datetime.now().isoformat()
        
        # 保存到文件
        file_path = os.path.join(self.conversations_dir, f"{conversation.id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(conversation.to_dict(), f, ensure_ascii=False, indent=2)
            
        # 更新内存中的对话
        self.conversations[conversation.id] = conversation
        return conversation
        
    def create_conversation(self, title=None, assistant_id=None):
        """创建新对话"""
        conversation = Conversation(title, assistant_id)
        self.current_conversation_id = conversation.id
        return self.save_conversation(conversation)
        
    def delete_conversation(self, conversation_id):
        """删除对话"""
        if conversation_id in self.conversations:
            file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            del self.conversations[conversation_id]
            
            # 如果删除的是当前对话，重置当前对话ID
            if self.current_conversation_id == conversation_id:
                self.current_conversation_id = None
                
            return True
        return False
        
    def get_conversation(self, conversation_id):
        """获取对话"""
        return self.conversations.get(conversation_id)
        
    def get_current_conversation(self):
        """获取当前对话"""
        if self.current_conversation_id:
            return self.get_conversation(self.current_conversation_id)
        return None
        
    def set_current_conversation(self, conversation_id):
        """设置当前对话"""
        if conversation_id in self.conversations:
            self.current_conversation_id = conversation_id
            return True
        return False
        
    def add_message_to_conversation(self, conversation_id, content, role="user"):
        """向对话添加消息"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            message = conversation.add_message(content, role)
            self.save_conversation(conversation)
            return message
        return None
        
    def add_message_to_current_conversation(self, content, role="user"):
        """向当前对话添加消息"""
        if not self.current_conversation_id:
            # 如果没有当前对话，创建一个新对话
            conversation = self.create_conversation()
            self.current_conversation_id = conversation.id
            
        return self.add_message_to_conversation(self.current_conversation_id, content, role)
        
    def get_all_conversations(self):
        """获取所有对话"""
        # 按更新时间排序
        return sorted(
            self.conversations.values(),
            key=lambda x: x.updated_at,
            reverse=True
        ) 
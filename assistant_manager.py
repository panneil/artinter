"""
助手管理器模块
支持预配置助手和自定义助手
"""

import os
import json
import uuid
from datetime import datetime

class Assistant:
    """助手类"""
    
    def __init__(self, name, description, model, provider, system_prompt=None, icon=None, id=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.model = model
        self.provider = provider  # 提供商类型，如"openai", "anthropic"等
        self.system_prompt = system_prompt or ""
        self.icon = icon or "🤖"
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "provider": self.provider,
            "system_prompt": self.system_prompt,
            "icon": self.icon,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
    @classmethod
    def from_dict(cls, data):
        """从字典创建助手"""
        assistant = cls(
            name=data.get("name", "未命名助手"),
            description=data.get("description", ""),
            model=data.get("model", ""),
            provider=data.get("provider", ""),
            system_prompt=data.get("system_prompt", ""),
            icon=data.get("icon", "🤖"),
            id=data.get("id")
        )
        assistant.created_at = data.get("created_at", assistant.created_at)
        assistant.updated_at = data.get("updated_at", assistant.updated_at)
        return assistant


class AssistantManager:
    """助手管理器类"""
    
    def __init__(self, config_dir):
        """初始化助手管理器"""
        self.config_dir = config_dir
        self.assistants_dir = os.path.join(config_dir, "assistants")
        self.assistants = {}
        self.default_assistants = {}
        
        # 创建助手目录
        if not os.path.exists(self.assistants_dir):
            os.makedirs(self.assistants_dir)
            
        # 加载助手
        self.load_assistants()
        
        # 创建默认助手
        self.create_default_assistants()
        
    def load_assistants(self):
        """加载所有助手"""
        # 加载用户创建的助手
        for filename in os.listdir(self.assistants_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.assistants_dir, filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        assistant = Assistant.from_dict(data)
                        self.assistants[assistant.id] = assistant
                except Exception as e:
                    print(f"加载助手失败 {filename}: {e}")
                    
    def save_assistant(self, assistant):
        """保存助手"""
        # 更新时间戳
        assistant.updated_at = datetime.now().isoformat()
        
        # 保存到文件
        file_path = os.path.join(self.assistants_dir, f"{assistant.id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(assistant.to_dict(), f, ensure_ascii=False, indent=2)
            
        # 更新内存中的助手
        self.assistants[assistant.id] = assistant
        return assistant
        
    def create_assistant(self, name, description, model, provider, system_prompt=None, icon=None):
        """创建新助手"""
        assistant = Assistant(name, description, model, provider, system_prompt, icon)
        return self.save_assistant(assistant)
        
    def delete_assistant(self, assistant_id):
        """删除助手"""
        if assistant_id in self.assistants:
            file_path = os.path.join(self.assistants_dir, f"{assistant_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            del self.assistants[assistant_id]
            return True
        return False
        
    def get_assistant(self, assistant_id):
        """获取助手"""
        # 先查找用户助手
        if assistant_id in self.assistants:
            return self.assistants[assistant_id]
            
        # 再查找默认助手
        if assistant_id in self.default_assistants:
            return self.default_assistants[assistant_id]
            
        return None
        
    def get_all_assistants(self):
        """获取所有助手"""
        # 合并用户助手和默认助手
        all_assistants = {}
        all_assistants.update(self.default_assistants)
        all_assistants.update(self.assistants)  # 用户助手优先
        return list(all_assistants.values())
        
    def create_default_assistants(self):
        """创建默认助手"""
        default_assistants = [
            {
                "id": "default-assistant",
                "name": "默认助手",
                "description": "通用对话助手，提供全面的对话支持",
                "model": "gpt-4o",
                "provider": "openai",
                "system_prompt": "你是一个有用的AI助手。",
                "icon": "🤖"
            },
            {
                "id": "code-assistant",
                "name": "编程助手",
                "description": "帮助编写、解释和调试代码",
                "model": "claude-3-opus-20240229",
                "provider": "anthropic",
                "system_prompt": "你是一个专业的编程助手，擅长编写代码、解释代码和调试程序。",
                "icon": "💻"
            },
            {
                "id": "ppt-generator",
                "name": "PPT生成器",
                "description": "快速生成精美PPT演示文稿",
                "model": "gemini-pro",
                "provider": "gemini",
                "system_prompt": "你是PPT生成助手，帮助用户创建专业、结构清晰的演示文稿。",
                "icon": "📊"
            },
            {
                "id": "web-developer",
                "name": "网页设计师",
                "description": "网页开发和设计专家",
                "model": "gpt-4o",
                "provider": "openai",
                "system_prompt": "你是网页设计和开发专家，帮助用户创建美观、功能强大的网站。",
                "icon": "🌐"
            },
            {
                "id": "image-describer",
                "name": "图像描述",
                "description": "详细描述和分析图像",
                "model": "claude-3-sonnet-20240229",
                "provider": "anthropic",
                "system_prompt": "你是图像分析专家，能详细描述和分析图像内容。",
                "icon": "🖼️"
            },
            {
                "id": "translator",
                "name": "翻译助手",
                "description": "多语言翻译专家",
                "model": "gpt-4o",
                "provider": "openai",
                "system_prompt": "你是翻译专家，能准确翻译各种语言的文本。",
                "icon": "🌐"
            },
            {
                "id": "writer-assistant",
                "name": "写作助手",
                "description": "提供写作建议和润色",
                "model": "claude-3-haiku-20240307",
                "provider": "anthropic",
                "system_prompt": "你是写作助手，帮助用户提高写作质量，提供润色和建议。",
                "icon": "✍️"
            },
            {
                "id": "local-model",
                "name": "本地模型",
                "description": "使用本地Ollama模型",
                "model": "llama3",
                "provider": "ollama",
                "system_prompt": "你是一个由Ollama提供支持的本地AI助手。",
                "icon": "🏠"
            }
        ]
        
        for assistant_data in default_assistants:
            assistant = Assistant.from_dict(assistant_data)
            self.default_assistants[assistant.id] = assistant 
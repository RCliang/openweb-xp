"""
MySQL 数据库初始化脚本
直接使用 SQLAlchemy 模型创建表，绕过 Alembic 迁移
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# 首先导入 db 模块创建引擎
from open_webui.internal.db import Base, engine

def init_database():
    """创建所有数据库表"""
    print("正在创建数据库表...")
    
    # 导入所有模型以确保它们被注册到 Base.metadata
    # 注意：不能导入 config，因为它会在导入时查询数据库
    import open_webui.models.users
    import open_webui.models.auths
    import open_webui.models.chats
    import open_webui.models.chat_messages
    import open_webui.models.files
    import open_webui.models.knowledge
    import open_webui.models.memories
    import open_webui.models.skills
    import open_webui.models.episodes
    import open_webui.models.tags
    import open_webui.models.functions
    import open_webui.models.models
    import open_webui.models.prompts
    import open_webui.models.tools
    import open_webui.models.groups
    import open_webui.models.folders
    import open_webui.models.channels
    import open_webui.models.notes
    import open_webui.models.messages
    import open_webui.models.feedbacks
    import open_webui.models.access_grants
    import open_webui.models.oauth_sessions
    import open_webui.models.prompt_history
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("数据库表创建完成！")

if __name__ == "__main__":
    init_database()

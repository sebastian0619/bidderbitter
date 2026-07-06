"""数据库模型"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean,
    DateTime, ForeignKey, JSON, Table, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

# ==================== 用户管理 ====================

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200))
    email = Column(String(200))
    role = Column(String(50), default="member")  # admin, member
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)
    
    # 关联
    projects = relationship("Project", back_populates="owner")
    uploaded_files = relationship("ManagedFile", back_populates="uploader")

# 文件-标签关联表
file_tags = Table(
    'file_tags',
    Base.metadata,
    Column('file_id', Integer, ForeignKey('managed_files.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=func.now())
)

# 项目-文件关联表
project_files = Table(
    'project_files',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    Column('file_id', Integer, ForeignKey('managed_files.id', ondelete='CASCADE'), primary_key=True),
    Column('section_type', String(50)),  # 章节类型: cover, qualification, performance, etc.
    Column('display_order', Integer, default=0),
    Column('created_at', DateTime, default=func.now())
)


class ManagedFile(Base):
    """文件管理表"""
    __tablename__ = "managed_files"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(300), nullable=False)
    display_name = Column(String(300), nullable=False)
    storage_path = Column(String(500), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 上传者

    # 文件信息
    file_type = Column(String(50))  # document, image, pdf
    mime_type = Column(String(100))
    file_size = Column(Integer)
    file_hash = Column(String(64))  # MD5

    # 业务分类
    category = Column(String(100))  # 合同、证书、业绩、奖项等
    description = Column(Text)
    keywords = Column(String(500))
    
    # 共享属性 - 业绩/证照等参考资料默认共享
    is_shared = Column(Boolean, default=True)  # 是否团队共享
    is_reference = Column(Boolean, default=False)  # 是否参考资料（业绩/证照等）

    # AI 分类结果
    ai_category = Column(String(100))  # AI 判断的分类
    ai_confidence = Column(Float)  # AI 置信度
    ai_analysis = Column(JSON)  # AI 分析详情

    # 处理状态
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")  # pending, analyzing, completed, failed

    # 使用统计
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)

    # 生命周期
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    tags = relationship("Tag", secondary=file_tags, back_populates="files")
    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan")
    managed_projects = relationship("Project", secondary=project_files, back_populates="managed_files")
    uploader = relationship("User", back_populates="uploaded_files")


class FileVersion(Base):
    """文件版本表"""
    __tablename__ = "file_versions"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("managed_files.id", ondelete="CASCADE"))
    version_number = Column(String(20), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    change_description = Column(Text)
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    file = relationship("ManagedFile", back_populates="versions")


class Tag(Base):
    """标签表"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(20), default="#409EFF")  # 默认蓝色
    category = Column(String(50))  # 标签分类: 业绩类型, 资质类型, 业务领域等
    created_at = Column(DateTime, default=func.now())

    files = relationship("ManagedFile", secondary=file_tags, back_populates="tags")


class Project(Base):
    """投标项目表"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)  # 项目名称
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 项目负责人
    tender_agency = Column(String(300))  # 招标代理机构
    tender_company = Column(String(300))  # 招标人
    bidder_name = Column(String(300))  # 投标人全称
    deadline = Column(DateTime)  # 投标截止日期
    status = Column(String(50), default="draft")  # 项目状态: draft, in_progress, completed
    description = Column(Text)  # 项目描述
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    owner = relationship("User", back_populates="projects")
    managed_files = relationship("ManagedFile", secondary=project_files, back_populates="managed_projects")
    sections = relationship("ProjectSection", back_populates="project", cascade="all, delete-orphan")


class ProjectSection(Base):
    """项目章节表"""
    __tablename__ = "project_sections"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    title = Column(String(200), nullable=False)  # 章节标题
    section_type = Column(String(50))  # 章节类型: cover, qualification, performance, award, etc.
    description = Column(Text)  # 章节描述
    order = Column(Integer, default=0)  # 排序
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    project = relationship("Project", back_populates="sections")
    documents = relationship("SectionDocument", back_populates="section", cascade="all, delete-orphan")


class SectionDocument(Base):
    """章节文档表"""
    __tablename__ = "section_documents"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("project_sections.id", ondelete="CASCADE"))
    file_id = Column(Integer, ForeignKey("managed_files.id", ondelete="CASCADE"))
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # 关联
    section = relationship("ProjectSection", back_populates="documents")
    file = relationship("ManagedFile")


# 数据库初始化
DATABASE_URL = "sqlite:///./bidtool.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

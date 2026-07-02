"""数据库模型"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean,
    DateTime, ForeignKey, JSON, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

# 文件-标签关联表
file_tags = Table(
    'file_tags',
    Base.metadata,
    Column('file_id', Integer, ForeignKey('managed_files.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=func.now())
)


class ManagedFile(Base):
    """文件管理表"""
    __tablename__ = "managed_files"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(300), nullable=False)
    display_name = Column(String(300), nullable=False)
    storage_path = Column(String(500), nullable=False)

    # 文件信息
    file_type = Column(String(50))  # document, image, pdf
    mime_type = Column(String(100))
    file_size = Column(Integer)
    file_hash = Column(String(64))  # MD5

    # 业务分类
    category = Column(String(100))  # 合同、证书、业绩、奖项等
    description = Column(Text)
    keywords = Column(String(500))

    # 处理状态
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")

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
    category = Column(String(50))  # 标签分类
    created_at = Column(DateTime, default=func.now())

    files = relationship("ManagedFile", secondary=file_tags, back_populates="tags")


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

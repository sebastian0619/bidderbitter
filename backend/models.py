from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Award(Base):
    """获奖信息表"""
    __tablename__ = "awards"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)  # 奖项名称
    brand = Column(String(100), nullable=False)  # 厂牌 (LegalBand, Chambers等)
    year = Column(Integer, nullable=False)  # 年份
    business_type = Column(String(200), nullable=False)  # 业务类型
    description = Column(Text)  # 奖项描述
    
    # 原始文档信息
    source_document = Column(String(500))  # 原始文档路径
    source_url = Column(String(1000))  # 获奖链接URL
    
    # 截图信息
    screenshot_path = Column(String(500))  # 截图保存路径
    screenshot_pages = Column(JSON)  # 截图分页信息
    
    # AI分析结果
    ai_analysis = Column(JSON)  # AI分析的结构化数据
    confidence_score = Column(Float)  # AI识别置信度
    
    # 状态信息
    is_verified = Column(Boolean, default=False)  # 是否已验证
    is_manual_input = Column(Boolean, default=False)  # 是否手动录入
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的文件
    files = relationship("AwardFile", back_populates="award")

class AwardFile(Base):
    """获奖相关文件表"""
    __tablename__ = "award_files"
    
    id = Column(Integer, primary_key=True, index=True)
    award_id = Column(Integer, ForeignKey("awards.id"))
    file_path = Column(String(500), nullable=False)  # 文件路径
    file_type = Column(String(50))  # 文件类型 (image, pdf, document)
    file_name = Column(String(255))  # 原始文件名
    file_size = Column(Integer)  # 文件大小
    page_number = Column(Integer)  # 页码（如果是多页文档）
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    award = relationship("Award", back_populates="files")

class Performance(Base):
    """业绩信息表"""
    __tablename__ = "performances"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(300), nullable=False)  # 聘用单位
    project_name = Column(String(500), nullable=False)  # 项目名称
    project_type = Column(String(100), nullable=False)  # 项目类型 (长期顾问/重大个案)
    business_field = Column(String(200), nullable=False)  # 业务领域
    
    # 时间信息
    start_date = Column(DateTime)  # 开始时间
    end_date = Column(DateTime)  # 结束时间
    year = Column(Integer, nullable=False)  # 年份
    
    # 金额信息
    contract_amount = Column(Float)  # 合同金额
    currency = Column(String(10), default="CNY")  # 货币单位
    
    # 项目描述
    description = Column(Text)  # 项目描述
    
    # 原始文档信息
    source_document = Column(String(500))  # 原始文档路径
    contract_file = Column(String(500))  # 合同文件路径
    
    # AI分析结果
    ai_analysis = Column(JSON)  # AI分析的结构化数据
    confidence_score = Column(Float)  # AI识别置信度
    
    # 状态信息
    is_verified = Column(Boolean, default=False)  # 是否已验证
    is_manual_input = Column(Boolean, default=False)  # 是否手动录入
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的文件
    files = relationship("PerformanceFile", back_populates="performance")

class PerformanceFile(Base):
    """业绩相关文件表"""
    __tablename__ = "performance_files"
    
    id = Column(Integer, primary_key=True, index=True)
    performance_id = Column(Integer, ForeignKey("performances.id"))
    file_path = Column(String(500), nullable=False)  # 文件路径
    file_type = Column(String(50))  # 文件类型 (contract, supporting_doc)
    file_name = Column(String(255))  # 原始文件名
    file_size = Column(Integer)  # 文件大小
    page_number = Column(Integer)  # 页码（如果是多页文档）
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    performance = relationship("Performance", back_populates="files")

class BusinessField(Base):
    """业务领域配置表"""
    __tablename__ = "business_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)  # 业务领域名称
    parent_id = Column(Integer, ForeignKey("business_fields.id"))  # 父级业务领域
    description = Column(Text)  # 描述
    is_active = Column(Boolean, default=True)  # 是否启用
    
    # 自引用关系
    children = relationship("BusinessField", backref="parent", remote_side=[id])
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Brand(Base):
    """厂牌配置表"""
    __tablename__ = "brands"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # 厂牌名称 
    full_name = Column(String(200))  # 厂牌全称
    description = Column(Text)  # 描述
    website = Column(String(500))  # 官网地址
    is_active = Column(Boolean, default=True)  # 是否启用
    
    created_at = Column(DateTime, default=datetime.utcnow)

class AIProcessLog(Base):
    """AI处理日志表"""
    __tablename__ = "ai_process_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), nullable=False)  # 任务类型 (ocr, analysis, extraction)
    source_file = Column(String(500))  # 源文件路径
    result = Column(JSON)  # 处理结果
    confidence_score = Column(Float)  # 置信度
    processing_time = Column(Float)  # 处理耗时(秒)
    
    # 关联信息
    award_id = Column(Integer, ForeignKey("awards.id"), nullable=True)
    performance_id = Column(Integer, ForeignKey("performances.id"), nullable=True)
    
    # 状态信息
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)  # 错误信息
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class SystemSettings(Base):
    """系统设置表"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)  # 设置键名
    setting_value = Column(Text)  # 设置值
    setting_type = Column(String(50), default="string")  # 设置类型: string, json, boolean, number
    category = Column(String(50), nullable=False)  # 设置分类: ai, upload, screenshot, etc.
    description = Column(Text)  # 设置描述
    is_sensitive = Column(Boolean, default=False)  # 是否敏感信息（如API密钥）
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 
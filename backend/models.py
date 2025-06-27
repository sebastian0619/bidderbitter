from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, JSON, func
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
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
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
    
    created_at = Column(DateTime, default=func.now())
    
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
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
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
    
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    performance = relationship("Performance", back_populates="files")

class LawyerCertificate(Base):
    """律师证信息表"""
    __tablename__ = "lawyer_certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    lawyer_name = Column(String(100), nullable=False)  # 律师姓名
    certificate_number = Column(String(100), nullable=False, unique=True)  # 执业证号
    law_firm = Column(String(300), nullable=False)  # 执业机构
    issuing_authority = Column(String(200))  # 发证机关（司法局/司法厅）
    
    # 个人信息
    age = Column(Integer)  # 年龄
    id_number = Column(String(20))  # 身份证号（脱敏显示）
    issue_date = Column(DateTime)  # 颁发日期
    
    # 职位和标签
    position = Column(String(50))  # 职位：合伙人/律师  
    position_tags = Column(JSON, default=list)  # 职位标签列表
    business_field_tags = Column(JSON, default=list)  # 业务领域标签列表
    custom_tags = Column(JSON, default=list)  # 自定义标签列表
    
    # 原始文档信息
    source_document = Column(String(500))  # 原始文档路径
    
    # AI分析结果
    ai_analysis = Column(JSON)  # AI分析的结构化数据
    confidence_score = Column(Float)  # AI识别置信度
    extracted_text = Column(Text)  # 提取的文本内容
    
    # 状态信息
    is_verified = Column(Boolean, default=False)  # 是否已验证
    is_manual_input = Column(Boolean, default=False)  # 是否手动录入
    verification_notes = Column(Text)  # 验证备注
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联的文件
    files = relationship("LawyerCertificateFile", back_populates="certificate")

class LawyerCertificateFile(Base):
    """律师证相关文件表"""
    __tablename__ = "lawyer_certificate_files"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey("lawyer_certificates.id"))
    file_path = Column(String(500), nullable=False)  # 文件路径
    file_type = Column(String(50))  # 文件类型 (original, scanned, cropped)
    file_name = Column(String(255))  # 原始文件名
    file_size = Column(Integer)  # 文件大小
    page_number = Column(Integer)  # 页码（如果是多页文档）
    
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    certificate = relationship("LawyerCertificate", back_populates="files")

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
    
    created_at = Column(DateTime, default=func.now())

class Brand(Base):
    """厂牌配置表"""
    __tablename__ = "brands"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # 厂牌名称 
    full_name = Column(String(200))  # 厂牌全称
    description = Column(Text)  # 描述
    website = Column(String(500))  # 官网地址
    is_active = Column(Boolean, default=True)  # 是否启用
    
    created_at = Column(DateTime, default=func.now())

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
    
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)

class SystemSettings(Base):
    """系统设置表"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)  # 设置键名
    setting_value = Column(Text)  # 设置值
    setting_type = Column(String(50), default="string")  # 设置类型: string, json, boolean, number, longtext
    category = Column(String(50), nullable=False)  # 设置分类: ai, upload, screenshot, etc.
    description = Column(Text)  # 设置描述
    is_sensitive = Column(Boolean, default=False)  # 是否敏感信息（如API密钥）
    is_editable = Column(Boolean, default=True)  # 是否可编辑
    requires_restart = Column(Boolean, default=False)  # 是否需要重启应用
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# 投标文件制作系统模型 - 开始

class Project(Base):
    """项目表"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)  # 项目名称
    tender_agency = Column(String(300))  # 招标代理机构
    tender_company = Column(String(300))  # 招标人
    bidder_name = Column(String(300))  # 投标人全称
    deadline = Column(DateTime)  # 投标截止日期
    status = Column(String(50), default="draft")  # 项目状态(draft/in_progress/completed)
    description = Column(Text)  # 项目描述
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    sections = relationship("ProjectSection", back_populates="project", cascade="all, delete-orphan")
    template_mappings = relationship("TemplateMapping", back_populates="project", cascade="all, delete-orphan")

class ProjectSection(Base):
    """项目章节表"""
    __tablename__ = "project_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String(200), nullable=False)  # 章节标题
    description = Column(Text)  # 章节描述
    order = Column(Integer, default=0)  # 排序
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    project = relationship("Project", back_populates="sections")
    documents = relationship("SectionDocument", back_populates="section", cascade="all, delete-orphan")
    data_mappings = relationship("SectionDataMapping", back_populates="section", cascade="all, delete-orphan")

class SectionDocument(Base):
    """章节文档表"""
    __tablename__ = "section_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("project_sections.id"))
    original_filename = Column(String(300))  # 原文件名
    storage_path = Column(String(500))  # 存储路径
    converted_path = Column(String(500))  # 转换后路径
    file_type = Column(String(50))  # 文件类型
    mime_type = Column(String(100))  # MIME类型
    order = Column(Integer, default=0)  # 文档排序
    page_count = Column(Integer)  # 页数
    file_size = Column(Integer)  # 文件大小(字节)
    is_processed = Column(Boolean, default=False)  # 是否已处理
    processing_status = Column(String(50), default="pending")  # 处理状态(pending/processing/completed/failed)
    error_message = Column(Text)  # 处理错误信息
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    section = relationship("ProjectSection", back_populates="documents")

class Template(Base):
    """模板表"""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # 模板名称
    type = Column(String(50))  # 模板类型(cover/seal/bid_form等)
    file_path = Column(String(500))  # 文件路径
    description = Column(Text)  # 模板描述
    is_default = Column(Boolean, default=False)  # 是否默认模板
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    fields = relationship("TemplateField", back_populates="template", cascade="all, delete-orphan")

class TemplateField(Base):
    """模板字段表"""
    __tablename__ = "template_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"))
    field_name = Column(String(100))  # 字段名
    field_key = Column(String(100))  # 字段唯一标识符
    field_type = Column(String(50))  # 字段类型(text/date/number)
    placeholder = Column(String(200))  # 占位符
    position = Column(JSON, nullable=True)  # 位置信息(x, y, width, height)
    is_required = Column(Boolean, default=False)  # 是否必填
    description = Column(Text)  # 字段描述
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    template = relationship("Template", back_populates="fields")

class TemplateMapping(Base):
    """模板字段映射表"""
    __tablename__ = "template_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    template_id = Column(Integer, ForeignKey("templates.id"))
    field_id = Column(Integer, ForeignKey("template_fields.id"))
    value = Column(Text)  # 填充的值
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    project = relationship("Project", back_populates="template_mappings")
    template = relationship("Template")
    field = relationship("TemplateField")

class GeneratedDocument(Base):
    """生成的文档表"""
    __tablename__ = "generated_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    filename = Column(String(300))  # 文件名
    file_path = Column(String(500))  # 文件路径
    file_size = Column(Integer)  # 文件大小
    page_count = Column(Integer)  # 页数
    generation_time = Column(Float)  # 生成用时(秒)
    created_at = Column(DateTime, default=func.now())
    
    # 关联
    project = relationship("Project")

# 新增：智能章节管理系统模型

class SectionType(Base):
    """章节类型表"""
    __tablename__ = "section_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # 章节类型名称
    display_name = Column(String(200))  # 显示名称
    description = Column(Text)  # 描述
    icon = Column(String(100))  # 图标
    color = Column(String(20))  # 颜色
    is_active = Column(Boolean, default=True)  # 是否启用
    
    # 关联的数据类型
    related_award_types = Column(JSON)  # 关联的奖项类型
    related_performance_types = Column(JSON)  # 关联的业绩类型
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SectionDataMapping(Base):
    """章节数据映射表"""
    __tablename__ = "section_data_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("project_sections.id"))
    
    # 数据类型和ID
    data_type = Column(String(50), nullable=False)  # award, performance
    data_id = Column(Integer, nullable=False)  # 对应的数据ID
    
    # 排序和显示设置
    display_order = Column(Integer, default=0)  # 显示顺序
    is_visible = Column(Boolean, default=True)  # 是否显示
    custom_title = Column(String(500))  # 自定义标题
    custom_description = Column(Text)  # 自定义描述
    
    # 关联条件
    filter_conditions = Column(JSON)  # 筛选条件
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    section = relationship("ProjectSection", back_populates="data_mappings")

# 新增：AI自动检索奖项系统模型

class DataSource(Base):
    """数据源配置表"""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # 数据源名称
    type = Column(String(50), nullable=False)  # 数据源类型 (chambers, legal500, etc.)
    base_url = Column(String(500), nullable=False)  # 基础URL
    description = Column(Text)  # 描述
    
    # 爬虫配置
    crawler_config = Column(JSON)  # 爬虫配置信息
    selectors = Column(JSON)  # CSS选择器配置
    rate_limit = Column(Integer, default=1)  # 请求频率限制(秒)
    
    # 状态信息
    is_active = Column(Boolean, default=True)  # 是否启用
    last_check = Column(DateTime)  # 最后检查时间
    status = Column(String(20), default="active")  # 状态
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SearchTask(Base):
    """搜索任务表"""
    __tablename__ = "search_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(200), nullable=False)  # 任务名称
    data_source_id = Column(Integer, ForeignKey("data_sources.id"))
    
    # 搜索参数
    law_firm_name = Column(String(300), nullable=False)  # 律师事务所名称
    search_year = Column(Integer, nullable=False)  # 搜索年份
    business_field = Column(String(200))  # 业务领域
    search_keywords = Column(JSON)  # 搜索关键词
    
    # 任务状态
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)  # 进度 0-100
    
    # 结果统计
    total_found = Column(Integer, default=0)  # 找到的总数
    processed_count = Column(Integer, default=0)  # 已处理数量
    success_count = Column(Integer, default=0)  # 成功数量
    error_count = Column(Integer, default=0)  # 错误数量
    
    # 执行信息
    started_at = Column(DateTime)  # 开始时间
    completed_at = Column(DateTime)  # 完成时间
    error_message = Column(Text)  # 错误信息
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    data_source = relationship("DataSource")
    results = relationship("SearchResult", back_populates="search_task")

class SearchResult(Base):
    """搜索结果表"""
    __tablename__ = "search_results"
    
    id = Column(Integer, primary_key=True, index=True)
    search_task_id = Column(Integer, ForeignKey("search_tasks.id"))
    
    # 原始搜索结果
    raw_data = Column(JSON)  # 原始数据
    source_url = Column(String(1000))  # 来源URL
    source_page = Column(String(500))  # 来源页面
    
    # 解析后的数据
    law_firm_name = Column(String(300))  # 律师事务所名称
    award_name = Column(String(500))  # 奖项名称
    award_year = Column(Integer)  # 获奖年份
    business_field = Column(String(200))  # 业务领域
    ranking = Column(String(100))  # 排名
    tier = Column(String(100))  # 等级
    
    # 处理状态
    status = Column(String(20), default="pending")  # pending, processed, imported, ignored
    confidence_score = Column(Float)  # 置信度
    
    # 关联到现有数据
    award_id = Column(Integer, ForeignKey("awards.id"), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    search_task = relationship("SearchTask", back_populates="results")
    award = relationship("Award")

# 新增：智能数据关联系统模型

class DataSimilarity(Base):
    """数据相似度表"""
    __tablename__ = "data_similarities"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 数据对
    data_type_1 = Column(String(50), nullable=False)  # 数据类型1
    data_id_1 = Column(Integer, nullable=False)  # 数据ID1
    data_type_2 = Column(String(50), nullable=False)  # 数据类型2
    data_id_2 = Column(Integer, nullable=False)  # 数据ID2
    
    # 相似度信息
    similarity_score = Column(Float, nullable=False)  # 相似度分数 0-1
    similarity_type = Column(String(50))  # 相似度类型 (content, field, client, etc.)
    similarity_details = Column(JSON)  # 相似度详情
    
    # 关联状态
    is_auto_linked = Column(Boolean, default=False)  # 是否自动关联
    is_manual_linked = Column(Boolean, default=False)  # 是否手动关联
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class RecommendationRule(Base):
    """推荐规则表"""
    __tablename__ = "recommendation_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # 规则名称
    description = Column(Text)  # 规则描述
    
    # 规则配置
    rule_type = Column(String(50), nullable=False)  # 规则类型
    conditions = Column(JSON, nullable=False)  # 触发条件
    actions = Column(JSON, nullable=False)  # 执行动作
    priority = Column(Integer, default=0)  # 优先级
    
    # 规则状态
    is_active = Column(Boolean, default=True)  # 是否启用
    execution_count = Column(Integer, default=0)  # 执行次数
    success_count = Column(Integer, default=0)  # 成功次数
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) 

# 新增：文件管理系统模型

class ManagedFile(Base):
    """文件管理表"""
    __tablename__ = "managed_files"
    
    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(300), nullable=False)  # 原始文件名
    display_name = Column(String(300), nullable=False)  # 显示名称
    storage_path = Column(String(500), nullable=False)  # 存储路径
    
    # 文件信息
    file_type = Column(String(50))  # 文件类型 (document, image, pdf, etc.)
    mime_type = Column(String(100))  # MIME类型
    file_size = Column(Integer)  # 文件大小(字节)
    file_hash = Column(String(64))  # 文件MD5哈希值，用于去重
    
    # 文件分类
    file_category = Column(String(50), nullable=False)  # 文件类型: temporary_upload, temporary_generated, permanent
    category = Column(String(100))  # 业务分类 (合同模板、证书文件、公司资料等)
    tags = Column(JSON)  # 标签数组
    
    # 元数据
    description = Column(Text)  # 文件描述
    keywords = Column(String(500))  # 关键词（空格分隔）
    
    # 处理状态
    is_processed = Column(Boolean, default=False)  # 是否已处理（OCR、格式转换等）
    processed_path = Column(String(500))  # 处理后文件路径
    processing_status = Column(String(50), default="pending")  # 处理状态
    processing_result = Column(JSON)  # 处理结果
    
    # 使用统计
    access_count = Column(Integer, default=0)  # 访问次数
    last_accessed = Column(DateTime)  # 最后访问时间
    
    # 生命周期管理
    expires_at = Column(DateTime)  # 过期时间（临时文件）
    is_archived = Column(Boolean, default=False)  # 是否已归档
    archived_at = Column(DateTime)  # 归档时间
    
    # 权限和可见性
    is_public = Column(Boolean, default=False)  # 是否公开（可在所有项目中使用）
    creator_id = Column(String(100))  # 创建者ID（预留用户系统）
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan")
    usages = relationship("FileUsage", back_populates="file", cascade="all, delete-orphan")

class FileVersion(Base):
    """文件版本表"""
    __tablename__ = "file_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("managed_files.id"))
    version_number = Column(String(20), nullable=False)  # 版本号 (1.0, 1.1, 2.0等)
    storage_path = Column(String(500), nullable=False)  # 版本文件路径
    file_size = Column(Integer)  # 文件大小
    file_hash = Column(String(64))  # 文件哈希值
    change_description = Column(Text)  # 变更说明
    is_current = Column(Boolean, default=True)  # 是否当前版本
    
    created_at = Column(DateTime, default=func.now())
    
    # 关联
    file = relationship("ManagedFile", back_populates="versions")

class FileUsage(Base):
    """文件使用记录表"""
    __tablename__ = "file_usages"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("managed_files.id"))
    
    # 使用场景
    usage_type = Column(String(50), nullable=False)  # 使用类型: conversion, project, template
    usage_context_id = Column(Integer)  # 使用上下文ID（项目ID、任务ID等）
    usage_context_type = Column(String(50))  # 使用上下文类型
    
    # 使用详情
    usage_description = Column(Text)  # 使用描述
    result_path = Column(String(500))  # 生成结果路径
    
    created_at = Column(DateTime, default=func.now())
    
    # 关联
    file = relationship("ManagedFile", back_populates="usages")

class FileCategory(Base):
    """文件分类表"""
    __tablename__ = "file_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # 分类名称
    display_name = Column(String(200))  # 显示名称
    parent_id = Column(Integer, ForeignKey("file_categories.id"))  # 父分类
    description = Column(Text)  # 分类描述
    icon = Column(String(100))  # 图标
    color = Column(String(20))  # 颜色
    
    # 分类设置
    is_active = Column(Boolean, default=True)  # 是否启用
    sort_order = Column(Integer, default=0)  # 排序
    allowed_extensions = Column(JSON)  # 允许的文件扩展名
    max_file_size = Column(Integer)  # 最大文件大小(字节)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 自引用关系
    children = relationship("FileCategory", backref="parent", remote_side=[id]) 
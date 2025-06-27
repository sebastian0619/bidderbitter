from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Base Response
class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None

# Award Schemas
class AwardBase(BaseModel):
    name: str
    issuing_organization: str
    award_date: datetime
    certificate_file: Optional[str] = None
    description: Optional[str] = None
    business_field: Optional[str] = None

class AwardCreate(AwardBase):
    pass

class AwardUpdate(BaseModel):
    name: Optional[str] = None
    issuing_organization: Optional[str] = None
    award_date: Optional[datetime] = None
    certificate_file: Optional[str] = None
    description: Optional[str] = None
    business_field: Optional[str] = None

class Award(AwardBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AwardResponse(BaseResponse):
    awards: List[Award]

# Performance Schemas
class PerformanceBase(BaseModel):
    project_name: str
    client_name: str
    project_amount: Optional[float] = None
    completion_date: datetime
    description: Optional[str] = None
    project_file: Optional[str] = None

class PerformanceCreate(PerformanceBase):
    pass

class PerformanceUpdate(BaseModel):
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    project_amount: Optional[float] = None
    completion_date: Optional[datetime] = None
    description: Optional[str] = None
    project_file: Optional[str] = None

class Performance(PerformanceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PerformanceResponse(BaseResponse):
    performances: List[Performance]

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    tender_company: Optional[str] = None
    tender_agency: Optional[str] = None
    bidder_name: str
    deadline: Optional[datetime] = None
    status: Optional[str] = 'draft'
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectResponse(BaseResponse):
    projects: List[Project]

# 新增：智能章节管理系统模式

class SectionTypeBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True
    related_award_types: Optional[List[str]] = None
    related_performance_types: Optional[List[str]] = None

class SectionTypeCreate(SectionTypeBase):
    pass

class SectionTypeUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    related_award_types: Optional[List[str]] = None
    related_performance_types: Optional[List[str]] = None

class SectionTypeResponse(SectionTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SectionDataMappingBase(BaseModel):
    data_type: str  # award, performance
    data_id: int
    display_order: int = 0
    is_visible: bool = True
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None
    filter_conditions: Optional[Dict[str, Any]] = None

class SectionDataMappingCreate(SectionDataMappingBase):
    pass

class SectionDataMappingUpdate(BaseModel):
    display_order: Optional[int] = None
    is_visible: Optional[bool] = None
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None
    filter_conditions: Optional[Dict[str, Any]] = None

class SectionDataMappingResponse(SectionDataMappingBase):
    id: int
    section_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SectionRecommendationRequest(BaseModel):
    section_title: Optional[str] = None
    section_description: Optional[str] = None
    business_field: Optional[str] = None
    search_year: Optional[int] = None
    project_id: Optional[int] = None

class SectionRecommendationResponse(BaseModel):
    awards: List[Award]
    performances: List[Performance]
    similar_sections: List[Dict[str, Any]]

# 新增：AI自动检索奖项系统模式

class DataSourceBase(BaseModel):
    name: str
    type: str  # chambers, legal500, etc.
    base_url: str
    description: Optional[str] = None
    crawler_config: Optional[Dict[str, Any]] = None
    selectors: Optional[Dict[str, Any]] = None
    rate_limit: int = 1
    is_active: bool = True

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    crawler_config: Optional[Dict[str, Any]] = None
    selectors: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None
    is_active: Optional[bool] = None

class DataSourceResponse(DataSourceBase):
    id: int
    status: str
    last_check: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SearchTaskBase(BaseModel):
    task_name: str
    data_source_id: int
    law_firm_name: str
    search_year: int
    business_field: Optional[str] = None
    search_keywords: Optional[List[str]] = None

class SearchTaskCreate(SearchTaskBase):
    pass

class SearchTaskResponse(SearchTaskBase):
    id: int
    status: str
    progress: float
    total_found: int
    processed_count: int
    success_count: int
    error_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SearchResultBase(BaseModel):
    search_task_id: int
    raw_data: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    source_page: Optional[str] = None
    law_firm_name: Optional[str] = None
    award_name: Optional[str] = None
    award_year: Optional[int] = None
    business_field: Optional[str] = None
    ranking: Optional[str] = None
    tier: Optional[str] = None
    status: str = "pending"
    confidence_score: Optional[float] = None
    award_id: Optional[int] = None

class SearchResultCreate(SearchResultBase):
    pass

class SearchResultResponse(SearchResultBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 新增：智能数据关联系统模式

class DataSimilarityBase(BaseModel):
    data_type_1: str
    data_id_1: int
    data_type_2: str
    data_id_2: int
    similarity_score: float
    similarity_type: Optional[str] = None
    similarity_details: Optional[Dict[str, Any]] = None
    is_auto_linked: bool = False
    is_manual_linked: bool = False

class DataSimilarityCreate(DataSimilarityBase):
    pass

class DataSimilarityResponse(DataSimilarityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RecommendationRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int = 0
    is_active: bool = True

class RecommendationRuleCreate(RecommendationRuleBase):
    pass

class RecommendationRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class RecommendationRuleResponse(RecommendationRuleBase):
    id: int
    execution_count: int
    success_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 系统设置相关Schema
class SystemSettingsBase(BaseModel):
    setting_key: str
    setting_value: str
    setting_type: str = "string"
    category: Optional[str] = None
    description: Optional[str] = None
    is_sensitive: bool = False

class SystemSettingsCreate(SystemSettingsBase):
    pass

class SystemSettingsUpdate(BaseModel):
    setting_value: Optional[str] = None
    setting_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None

class SystemSettingsResponse(SystemSettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 品牌相关Schema
class BrandBase(BaseModel):
    name: str
    full_name: Optional[str] = None
    website: Optional[str] = None
    is_active: bool = True

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BaseModel):
    full_name: Optional[str] = None
    website: Optional[str] = None
    is_active: Optional[bool] = None

class BrandResponse(BrandBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 业务领域相关Schema
class BusinessFieldBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class BusinessFieldCreate(BusinessFieldBase):
    pass

class BusinessFieldUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None

class BusinessFieldResponse(BusinessFieldBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 

# 律师证相关Schema
class LawyerCertificateBase(BaseModel):
    lawyer_name: str
    certificate_number: str
    law_firm: str
    issuing_authority: Optional[str] = None
    age: Optional[int] = None
    id_number: Optional[str] = None
    issue_date: Optional[datetime] = None
    position: Optional[str] = "律师"
    position_tags: Optional[List[str]] = []
    business_field_tags: Optional[List[str]] = []
    custom_tags: Optional[List[str]] = []
    verification_notes: Optional[str] = None

class LawyerCertificateCreate(LawyerCertificateBase):
    pass

class LawyerCertificateUpdate(BaseModel):
    lawyer_name: Optional[str] = None
    certificate_number: Optional[str] = None
    law_firm: Optional[str] = None
    issuing_authority: Optional[str] = None
    age: Optional[int] = None
    id_number: Optional[str] = None
    issue_date: Optional[datetime] = None
    position: Optional[str] = None
    position_tags: Optional[List[str]] = None
    business_field_tags: Optional[List[str]] = None
    custom_tags: Optional[List[str]] = None
    is_verified: Optional[bool] = None
    verification_notes: Optional[str] = None

class LawyerCertificateResponse(LawyerCertificateBase):
    id: int
    source_document: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    extracted_text: Optional[str] = None
    is_verified: bool = False
    is_manual_input: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LawyerCertificateFileBase(BaseModel):
    file_path: str
    file_type: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    page_number: Optional[int] = None

class LawyerCertificateFileCreate(LawyerCertificateFileBase):
    certificate_id: int

class LawyerCertificateFileResponse(LawyerCertificateFileBase):
    id: int
    certificate_id: int
    created_at: datetime

    class Config:
        from_attributes = True 
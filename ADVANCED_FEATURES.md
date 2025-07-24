# BidderBitter 高级功能说明

## 概述

BidderBitter 法律行业投标软件系统现已支持以下高级功能：

1. **智能章节管理系统** - 支持章节类型管理、数据映射和智能推荐
2. **AI自动检索奖项系统** - 自动从权威法律评级网站检索奖项信息
3. **智能数据关联系统** - 跨模块数据关联和相似度分析
4. **高级搜索和分析系统** - 语义搜索和多维度筛选

## 功能详解

### 1. 智能章节管理系统

#### 功能特点
- **章节类型管理**: 支持自定义章节类型，如"荣誉奖项"、"业绩案例"、"团队介绍"等
- **数据映射**: 在项目管理中直接关联奖项和业绩数据
- **智能推荐**: 基于章节要求自动推荐最相关的数据
- **拖拽关联**: 支持拖拽方式关联章节和数据

#### 使用方法
1. 访问 `/section-manager` 页面
2. 在左侧管理章节类型
3. 在中间选择项目和章节
4. 在右侧进行数据映射和查看推荐

#### 章节类型
- **荣誉奖项**: 律师事务所获得的各类荣誉和奖项
- **业绩案例**: 律师事务所完成的重要项目和案例
- **团队介绍**: 律师事务所团队成员的介绍和背景
- **服务领域**: 律师事务所提供的法律服务领域
- **客户推荐**: 客户对律师事务所的评价和推荐

### 2. AI自动检索奖项系统

#### 功能特点
- **多源数据检索**: 支持钱伯斯、Legal 500、IFLR1000等权威法律评级网站
- **智能爬虫**: 使用Selenium + AI识别网页结构变化
- **精确检索**: 根据律师事务所名称、年份、业务领域进行精确检索
- **批量检索**: 支持批量检索多个机构或年份
- **数据验证**: 自动验证检索结果的准确性和完整性

#### 使用方法
1. 访问 `/award-search` 页面
2. 在左侧配置搜索参数
3. 点击"开始搜索"创建搜索任务
4. 在中间查看搜索任务状态
5. 在右侧查看和导入搜索结果

#### 支持的数据源
- **Chambers**: 全球权威的法律服务评级机构
- **Legal 500**: 全球领先的法律服务指南
- **IFLR1000**: 专注于金融法律领域的权威评级机构

#### 搜索参数
- **律师事务所名称**: 必填，要搜索的律师事务所名称
- **搜索年份**: 必填，要搜索的年份
- **业务领域**: 可选，限制搜索的业务领域
- **搜索关键词**: 可选，额外的搜索关键词

### 3. 智能数据关联系统

#### 功能特点
- **跨模块数据关联**: 项目管理、奖项管理、业绩管理之间的智能关联
- **相似度匹配**: 使用AI算法匹配相似的项目和奖项
- **推荐引擎**: 基于历史数据推荐最合适的奖项和业绩组合
- **数据去重**: 自动识别和合并重复数据

#### 推荐规则
1. **同领域奖项推荐**: 基于业务领域推荐相关奖项
2. **时间相关性推荐**: 基于时间相关性推荐奖项和业绩
3. **相似项目推荐**: 基于相似项目推荐相关数据

### 4. 高级搜索和分析系统

#### 功能特点
- **语义搜索**: 支持自然语言搜索奖项和业绩信息
- **多维度筛选**: 按时间、机构、金额、业务领域等多维度筛选
- **统计分析**: 提供数据统计和分析功能
- **趋势分析**: 分析获奖和业绩的时间趋势

## 技术架构

### 后端技术栈
- **FastAPI**: Web框架
- **SQLAlchemy**: ORM框架
- **PostgreSQL**: 主数据库
- **Redis**: 缓存和任务队列
- **Selenium**: Web自动化
- **OpenAI API**: AI分析和推荐
- **scikit-learn**: 机器学习算法

### 前端技术栈
- **Vue 3**: 前端框架
- **Element Plus**: UI组件库
- **Pinia**: 状态管理
- **Vue Router**: 路由管理
- **Axios**: HTTP客户端

### 新增数据模型

#### 智能章节管理
- `SectionType`: 章节类型表
- `SectionDataMapping`: 章节数据映射表

#### AI自动检索
- `DataSource`: 数据源配置表
- `SearchTask`: 搜索任务表
- `SearchResult`: 搜索结果表

#### 智能数据关联
- `DataSimilarity`: 数据相似度表
- `RecommendationRule`: 推荐规则表

## 部署说明

### 环境要求
- Python 3.13+
- Node.js 18+
- PostgreSQL 12+
- Redis 6+
- Chrome/Chromium (用于Selenium)

### 安装依赖
```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 数据库初始化
```bash
# 运行数据库迁移
cd backend
python -m alembic upgrade head

# 初始化高级功能数据
python init_advanced_data.py
```

### 启动服务
```bash
# 使用Docker Compose
docker-compose up -d

# 或使用Podman
podman-compose up -d
```

## 配置说明

### 数据源配置
在 `DataSource` 表中配置各个法律评级网站的爬虫参数：

```json
{
  "crawler_config": {
    "search_url": "https://chambers.com/legal-guide/search",
    "firm_page_pattern": "https://chambers.com/legal-guide/firm/*",
    "wait_time": 2,
    "max_retries": 3
  },
  "selectors": {
    "firm_list": ".firm-item",
    "firm_name": ".firm-name",
    "award_list": ".award-item",
    "award_name": ".award-name",
    "award_year": ".award-year",
    "business_field": ".business-field",
    "ranking": ".ranking"
  }
}
```

### 推荐规则配置
在 `RecommendationRule` 表中配置推荐规则：

```json
{
  "conditions": {
    "trigger": "section_creation",
    "field_match": true,
    "year_range": 3
  },
  "actions": {
    "recommend_awards": true,
    "recommend_performances": false,
    "max_recommendations": 10,
    "sort_by": "year_desc"
  }
}
```

## API文档

### 智能章节管理API
- `GET /api/sections/types` - 获取章节类型列表
- `POST /api/sections/types` - 创建章节类型
- `GET /api/sections/{section_id}/mappings` - 获取章节数据映射
- `POST /api/sections/{section_id}/mappings` - 创建数据映射
- `POST /api/sections/recommendations` - 获取智能推荐

### AI自动检索API
- `GET /api/search/sources` - 获取数据源列表
- `POST /api/search/tasks` - 创建搜索任务
- `GET /api/search/tasks` - 获取搜索任务列表
- `GET /api/search/results` - 获取搜索结果
- `POST /api/search/results/{result_id}/import` - 导入搜索结果

## 注意事项

### 爬虫使用注意事项
1. **访问频率限制**: 请遵守各网站的robots.txt和使用条款
2. **反爬虫策略**: 系统已内置反爬虫检测和应对机制
3. **数据准确性**: 建议人工验证重要的检索结果
4. **网站结构变化**: 定期检查网站结构变化，及时更新选择器配置

### 性能优化
1. **缓存机制**: 系统已实现搜索结果缓存
2. **并发控制**: 限制同时进行的搜索任务数量
3. **数据库优化**: 建议定期清理历史数据
4. **资源监控**: 监控系统资源使用情况

### 安全考虑
1. **访问权限**: 建议配置适当的访问权限控制
2. **数据保护**: 敏感数据加密存储
3. **日志记录**: 记录所有操作日志
4. **备份策略**: 定期备份重要数据

## 故障排除

### 常见问题
1. **爬虫失败**: 检查网络连接和网站可访问性
2. **数据导入失败**: 检查数据格式和数据库连接
3. **推荐不准确**: 调整推荐规则参数
4. **性能问题**: 检查系统资源和配置

### 日志查看
```bash
# 查看后端日志
docker logs bidder-backend

# 查看前端日志
docker logs bidder-frontend
```

## 更新日志

### v2.0.0 (2024-01-XX)
- 新增智能章节管理系统
- 新增AI自动检索奖项系统
- 新增智能数据关联系统
- 新增高级搜索和分析系统
- 优化用户界面和用户体验
- 增强数据安全和性能

## 技术支持

如有问题或建议，请联系开发团队或提交Issue。 
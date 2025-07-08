# 投标软件系统 (BidderBitter)

一个专为法律行业设计的投标资料管理和文档生成系统。

## 功能特性

### 🏆 获奖信息管理
- **智能文档解析**：支持上传Word、PDF文档，AI自动提取获奖信息
- **网页截图功能**：自动爬取获奖链接页面，生成高质量长截图
- **多厂牌支持**：支持19个主流法律评级机构
  - 国际机构：Chambers、Legal 500、IFLR、Who's Who Legal、Best Lawyers
  - 亚太机构：ALB、Legal Band、Asialaw、China Law & Practice
  - 专业机构：IAM、Global Arbitration Review、Global Competition Review
  - 其他重要评级：Benchmark Litigation、CBLJ等
- **分类管理**：按厂牌、年份、业务类型进行智能分类
- **手动录入**：支持手动添加和编辑获奖信息
- **数据验证**：AI置信度评估，确保数据准确性

### 📊 业绩信息管理
- **业绩录入**：支持长期顾问和重大个案两种类型
- **合同解析**：OCR识别合同文档，自动提取关键信息
- **项目分类**：按业务领域、年份、项目类型分类管理，涵盖70+专业业务领域
  - 公司法律服务：公司业务、并购重组、外商投资、私募股权等
  - 金融法律服务：银行金融、资本市场、资产证券化、REITs等
  - 争议解决：国际仲裁、商事仲裁、诉讼代理、跨境争议等
  - 专业法律领域：知识产权、反不正当竞争、娱乐法、体育法等
  - 新兴业务：医疗健康、人工智能、区块链、金融科技等
  - 跨境业务：境外上市、一带一路、跨境投资、国际制裁等
- **金额管理**：支持多币种合同金额记录
- **文档关联**：业绩记录可关联原始合同文件

### 📄 文档生成功能
- **专业Word文档**：生成符合投标要求的专业文档
- **灵活筛选**：按厂牌、业务领域、年份等条件筛选
- **图片优化**：自动调整图片尺寸适配A4纸张
- **多种模式**：支持获奖文档、业绩文档、综合文档生成
- **分页处理**：长截图自动分页，确保阅读体验

### 🤖 AI智能能力
- **OCR文字识别**：支持中英文混合识别
- **语义理解**：智能理解文档内容并提取关键信息
- **图像分析**：分析获奖证书和法律文档图片
- **数据结构化**：将非结构化文档转换为结构化数据

## 技术架构

### 后端技术栈
- **FastAPI**：现代Python Web框架
- **SQLAlchemy**：ORM数据库操作
- **PostgreSQL**：主数据库
- **Redis**：缓存和队列
- **OpenAI API**：AI能力支持
- **Selenium**：网页自动化和截图
- **Tesseract**：OCR文字识别
- **python-docx**：Word文档生成

### 前端技术栈
- **Vue 3**：渐进式JavaScript框架
- **Element Plus**：UI组件库
- **Vite**：构建工具
- **Pinia**：状态管理
- **Vue Router**：路由管理
- **Axios**：HTTP客户端

### 基础设施
- **Docker**：容器化部署
- **Docker Compose**：多容器编排
- **Nginx**：反向代理和静态文件服务
- **Chrome WebDriver**：无头浏览器支持

## 快速开始

### 环境要求
- Docker 和 Docker Compose
- 至少4GB可用内存
- OpenAI API Key（可选，用于AI功能）

### 🚀 使用Public镜像启动 (推荐)

**无需构建，直接使用预构建的镜像！**

```bash
# 克隆项目
git clone https://github.com/sebastian0619/bidderbitter.git
cd bidderbitter

# 使用Public镜像启动 (无需认证)
./start-public.sh

# 或者手动启动
docker-compose -f docker-compose.ghcr.yml up -d
```

**访问系统**
- 前端界面：http://localhost:5555
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 🔧 本地构建启动

1. **克隆项目**
```bash
git clone https://github.com/sebastian0619/bidderbitter.git
cd bidderbitter
```

2. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（可选）
# 主要配置OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
```

3. **启动服务**
```bash
# 构建和启动所有服务
docker-compose up -d

# 查看启动状态
docker-compose ps
```

4. **访问系统**
- 前端界面：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 开发环境

如果需要本地开发，可以分别启动前后端：

**后端开发**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**前端开发**
```bash
cd frontend
npm install
npm run dev
```

## 使用指南

### 1. 初始设置
- 访问系统设置页面，配置厂牌和业务领域
- 如需AI功能，请确保配置了OpenAI API Key

### 2. 获奖信息管理
1. **文档上传**：在"获奖管理 > 上传获奖文档"上传Word/PDF文件
2. **AI分析**：系统自动分析文档并提取获奖信息
3. **截图处理**：对于包含链接的获奖，系统会自动截图保存
4. **数据验证**：检查AI提取的数据，必要时手动修正
5. **手动录入**：也可直接手动录入获奖信息

### 3. 业绩信息管理
1. **上传合同**：上传业绩相关的合同或说明文档
2. **信息提取**：AI自动提取客户、项目、金额等信息
3. **分类管理**：按业务领域和项目类型分类
4. **数据完善**：补充合同金额、服务期限等详细信息

### 4. 文档生成
1. **选择类型**：选择生成获奖文档、业绩文档或综合文档
2. **设置筛选**：按厂牌、业务领域、年份等条件筛选
3. **生成文档**：系统自动生成Word文档
4. **下载使用**：下载生成的文档用于投标

## 项目结构

```
bidderbitter/
├── backend/                    # 后端代码
│   ├── main.py                # FastAPI主应用
│   ├── models.py              # 数据库模型
│   ├── database.py            # 数据库配置
│   ├── ai_service.py          # AI服务模块
│   ├── screenshot_service.py  # 截图服务模块
│   ├── document_generator.py  # 文档生成模块
│   ├── requirements.txt       # Python依赖
│   └── Dockerfile            # 后端Docker配置
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 公共组件
│   │   ├── services/         # API服务
│   │   ├── stores/           # 状态管理
│   │   └── styles/           # 样式文件
│   ├── package.json          # 前端依赖
│   ├── vite.config.js        # Vite配置
│   └── Dockerfile            # 前端Docker配置
├── docker-compose.yml         # Docker编排配置
├── init.sql                  # 数据库初始化脚本
└── README.md                 # 项目说明文档
```

## AI提示词参考

系统内置了专业的AI提示词来分析法律行业文档：

### 获奖分析提示词
```
你是一个专业的法律行业获奖信息分析专家。请分析以下文档内容，提取获奖相关信息。

请按照以下JSON格式返回结果：
{
    "awards": [
        {
            "title": "奖项名称",
            "brand": "厂牌名称（如Chambers, Legal Band等）",
            "year": 年份,
            "business_type": "业务类型（如银行与金融、资本市场等）",
            "description": "获奖描述",
            "url": "相关链接（如果有）",
            "confidence": 置信度(0-1)
        }
    ],
    "confidence": 整体置信度(0-1)
}

注意：
1. 如果文档中包含多个奖项，请全部提取
2. 厂牌名称请标准化（如Chambers and Partners写作Chambers）
3. 业务类型请使用标准分类
4. 如果某些信息不确定，请在confidence中体现
```

### 业绩分析提示词
```
你是一个专业的法律服务业绩信息分析专家。请分析以下文档内容，提取业绩相关信息。

请按照以下JSON格式返回结果：
{
    "performances": [
        {
            "client_name": "客户名称",
            "project_name": "项目名称",
            "project_type": "项目类型（长期顾问/重大个案）",
            "business_field": "业务领域",
            "start_date": "开始日期（YYYY-MM-DD格式）",
            "end_date": "结束日期（YYYY-MM-DD格式）",
            "year": 年份,
            "contract_amount": 合同金额,
            "currency": "货币单位",
            "description": "项目描述",
            "confidence": 置信度(0-1)
        }
    ],
    "confidence": 整体置信度(0-1)
}

注意：
1. 如果是合同文档，重点提取合同金额、服务期限等信息
2. 如果是业绩汇总文档，提取所有项目信息
3. 日期格式请统一为YYYY-MM-DD
4. 金额请提取数字部分，货币单位单独标注
```

## 常见问题

### Q: AI功能无法使用怎么办？
A: 请检查是否正确配置了OpenAI API Key，系统也支持不使用AI功能的纯手动模式。

### Q: 截图功能失效怎么处理？
A: 检查Chrome容器是否正常启动，或者可以手动上传截图文件。

### Q: 生成的Word文档格式不正确？
A: 确保上传的截图尺寸合适，系统会自动优化图片以适配A4纸张。

### Q: 如何备份数据？
A: 可以使用Docker命令备份PostgreSQL数据库，或者通过系统导出功能。

## 🐳 自动构建

本项目使用GitHub Actions自动构建Docker镜像：

- **触发条件**: 每次push到main/master/develop分支
- **镜像仓库**: GitHub Container Registry (ghcr.io)
- **镜像权限**: **PUBLIC** - 任何人都可以拉取使用
- **标签策略**: latest, {branch-name}, {commit-sha}

### 镜像地址
```
ghcr.io/sebastian0619/bidderbitter/backend:latest
ghcr.io/sebastian0619/bidderbitter/frontend:latest
```

### 手动拉取
```bash
# 无需认证，直接拉取
docker pull ghcr.io/sebastian0619/bidderbitter/backend:latest
docker pull ghcr.io/sebastian0619/bidderbitter/frontend:latest
```

详细说明请查看 [GitHub Actions 指南](GITHUB_ACTIONS_GUIDE.md)

## 开发计划

- [ ] 支持更多文档格式（Excel、PPT等）
- [ ] 添加数据统计和分析功能
- [ ] 支持多语言界面
- [ ] 集成更多AI服务商
- [ ] 添加协作功能

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或Pull Request。


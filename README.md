# BidTool - 投标文件工具

简单高效的投标文件准备工具，支持文件管理、PDF 处理、标签分类等功能。

## 功能特性

- **文件管理**: 上传、下载、预览、删除文件
- **标签系统**: 为文件添加标签，支持分类和筛选
- **PDF 工具**: PDF 合并、图片提取、图片转 PDF
- **Web UI**: 基于 Vue 3 + Element Plus 的现代化界面

## 技术栈

- **后端**: FastAPI + SQLite + SQLAlchemy
- **前端**: Vue 3 + Element Plus + Vite
- **部署**: Docker + Docker Compose

## 快速开始

### 使用 Docker Compose (推荐)

```bash
# 克隆项目
git clone https://github.com/sebastian0619/bidderbitter.git
cd bidderbitter

# 启动服务
docker-compose up -d

# 访问前端
# http://localhost:3000

# 访问后端 API 文档
# http://localhost:8000/docs
```

### 本地开发

#### 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## API 文档

启动后端后访问 http://localhost:8000/docs 查看 Swagger API 文档。

## 项目结构

```
bidtool/
├── backend/                 # 后端代码
│   ├── main.py             # FastAPI 主应用
│   ├── models.py           # 数据库模型
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile          # 后端 Docker 配置
├── frontend/                # 前端代码
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 公共组件
│   │   ├── services/       # API 服务
│   │   └── router/         # 路由配置
│   ├── package.json        # 前端依赖
│   └── Dockerfile          # 前端 Docker 配置
├── docker-compose.yml       # Docker 编排配置
└── README.md               # 项目说明
```

## 功能说明

### 文件管理

- 支持上传任意文件类型
- 文件自动分类（PDF、图片、文档）
- 支持文件预览和下载
- 文件版本管理

### 标签系统

- 创建自定义标签
- 为文件添加多个标签
- 按标签筛选文件
- 标签颜色自定义

### PDF 工具

- **PDF 合并**: 选择多个 PDF 文件合并为一个
- **PDF 图片提取**: 从 PDF 中提取所有图片
- **图片转 PDF**: 将多张图片合并为 PDF

## 开发计划

- [x] 后端 API 开发
- [x] 前端 UI 开发
- [ ] 文件预览功能
- [ ] 批量操作
- [ ] 高级搜索
- [ ] 用户权限管理
- [ ] API 认证

## 许可证

MIT License

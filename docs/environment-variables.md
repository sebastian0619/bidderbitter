# 环境变量配置说明

投标软件系统支持通过环境变量进行灵活配置，以下是所有可配置的环境变量说明。

## 🗂️ 配置分类

### 📊 数据库配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `DATABASE_URL` | `postgresql://bidder_user:bidder_pass@postgres:5432/bidder_db` | PostgreSQL数据库连接URL |
| `REDIS_URL` | `redis://redis:6379` | Redis缓存服务连接URL |

### 🤖 AI服务配置

#### 基础设置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `AI_PROVIDER` | `openai` | AI服务提供商：`openai`、`azure`、`anthropic`、`google`、`custom` |
| `ENABLE_AI` | `true` | 是否启用AI功能 |

#### OpenAI配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OPENAI_API_KEY` | 空 | **必填** OpenAI API密钥 |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API基础URL |
| `OPENAI_MODEL` | `gpt-4` | 用于文本分析的模型 |
| `OPENAI_VISION_MODEL` | `gpt-4-vision-preview` | 用于图像分析的模型 |

#### Azure OpenAI配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `AZURE_OPENAI_API_KEY` | 空 | Azure OpenAI API密钥 |
| `AZURE_OPENAI_ENDPOINT` | 空 | Azure OpenAI服务端点 |
| `AZURE_OPENAI_API_VERSION` | `2024-02-01` | Azure OpenAI API版本 |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | 空 | 文本模型部署名称 |
| `AZURE_OPENAI_VISION_DEPLOYMENT_NAME` | 空 | 视觉模型部署名称 |

#### 其他AI服务配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `ANTHROPIC_API_KEY` | 空 | Anthropic Claude API密钥 |
| `GOOGLE_API_KEY` | 空 | Google AI API密钥 |
| `CUSTOM_AI_API_KEY` | 空 | 自定义AI服务API密钥 |
| `CUSTOM_AI_BASE_URL` | 空 | 自定义AI服务基础URL |

### 📸 截图服务配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `SELENIUM_HUB_URL` | `http://chrome:4444/wd/hub` | Selenium WebDriver服务地址 |
| `ENABLE_SCREENSHOT` | `true` | 是否启用网页截图功能 |
| `SCREENSHOT_TIMEOUT` | `30` | 截图超时时间（秒） |
| `SCREENSHOT_MAX_PAGES` | `20` | 单个页面最大截图页数 |

### 📁 文件上传配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `MAX_FILE_SIZE` | `52428800` | 最大文件大小（字节，默认50MB） |
| `ALLOWED_FILE_TYPES` | `pdf,docx,doc,png,jpg,jpeg` | 允许上传的文件类型 |
| `UPLOAD_PATH` | `/app/uploads` | 上传文件存储路径 |
| `SCREENSHOT_PATH` | `/app/screenshots` | 截图文件存储路径 |
| `GENERATED_DOCS_PATH` | `/app/generated_docs` | 生成文档存储路径 |

### ⚙️ 应用配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `APP_ENV` | `production` | 应用运行环境：`development`、`production` |
| `LOG_LEVEL` | `INFO` | 日志级别：`DEBUG`、`INFO`、`WARNING`、`ERROR` |
| `DEBUG` | `false` | 是否启用调试模式 |
| `SECRET_KEY` | `your-secret-key-change-in-production` | **必须修改** 应用安全密钥 |

### 🔧 功能开关
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `ENABLE_AI` | `true` | 启用AI分析功能 |
| `ENABLE_OCR` | `true` | 启用OCR文字识别功能 |
| `ENABLE_DOCUMENT_GENERATION` | `true` | 启用文档生成功能 |

### 👁️ OCR配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OCR_LANGUAGES` | `chi_sim+eng` | OCR识别语言（中文简体+英文） |
| `OCR_ENGINE` | `tesseract` | OCR引擎类型 |

### 📄 文档生成配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `WORD_TEMPLATE_PATH` | `/app/templates` | Word模板文件路径 |
| `DEFAULT_FONT` | `Microsoft YaHei` | 默认字体 |
| `IMAGE_MAX_WIDTH` | `1654` | 图片最大宽度（像素，A4纸宽度） |
| `IMAGE_QUALITY` | `85` | 图片压缩质量（1-100） |

### 🚀 性能配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `WORKER_CONNECTIONS` | `1000` | 工作进程连接数 |
| `MAX_CONCURRENT_REQUESTS` | `100` | 最大并发请求数 |
| `REQUEST_TIMEOUT` | `300` | 请求超时时间（秒） |

### 🔒 安全配置
| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `ALLOWED_HOSTS` | `*` | 允许的主机名，生产环境建议设置具体值 |
| `CORS_ORIGINS` | `http://localhost:3000,http://frontend:3000` | 允许的跨域来源 |

## 🛠️ 配置示例

### 基础配置（仅OpenAI）
```bash
# 必须配置
OPENAI_API_KEY=sk-your-openai-api-key-here
SECRET_KEY=your-unique-secret-key-here

# 可选配置
AI_PROVIDER=openai
ENABLE_AI=true
LOG_LEVEL=INFO
```

### Azure OpenAI配置
```bash
# 使用Azure OpenAI
AI_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-azure-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_VISION_DEPLOYMENT_NAME=gpt-4-vision
```

### 自定义AI服务配置
```bash
# 使用兼容OpenAI API的自定义服务
AI_PROVIDER=custom
CUSTOM_AI_API_KEY=your-custom-api-key
CUSTOM_AI_BASE_URL=https://your-custom-ai-service.com/v1
```

### 生产环境安全配置
```bash
# 安全配置示例
SECRET_KEY=randomly-generated-secret-key-32-chars
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com
DEBUG=false
LOG_LEVEL=WARNING
```

### 性能优化配置
```bash
# 高性能配置
MAX_CONCURRENT_REQUESTS=200
WORKER_CONNECTIONS=2000
REQUEST_TIMEOUT=600
MAX_FILE_SIZE=104857600  # 100MB
```

## 📋 配置检查清单

### 部署前必须配置
- [ ] `OPENAI_API_KEY` 或对应AI服务的API密钥
- [ ] `SECRET_KEY` 修改为随机生成的安全密钥
- [ ] `ALLOWED_HOSTS` 设置为实际域名（生产环境）
- [ ] `CORS_ORIGINS` 设置为实际前端域名

### 推荐配置
- [ ] 根据实际需求调整 `MAX_FILE_SIZE`
- [ ] 根据服务器性能调整 `MAX_CONCURRENT_REQUESTS`
- [ ] 设置合适的 `LOG_LEVEL`
- [ ] 配置备用AI服务提供商

### 功能测试
- [ ] 测试AI文档分析功能
- [ ] 测试网页截图功能
- [ ] 测试文档生成功能
- [ ] 测试文件上传功能

## 🔍 故障排除

### AI功能不工作
1. 检查 `ENABLE_AI=true`
2. 验证API密钥正确性
3. 检查网络连接和防火墙设置
4. 查看后端日志：`docker-compose logs backend`

### 截图功能失败
1. 检查 `ENABLE_SCREENSHOT=true`
2. 验证Chrome容器运行状态：`docker-compose ps chrome`
3. 检查网络连接
4. 增加 `SCREENSHOT_TIMEOUT` 值

### 文件上传问题
1. 检查文件大小是否超过 `MAX_FILE_SIZE`
2. 验证文件类型在 `ALLOWED_FILE_TYPES` 中
3. 检查磁盘空间
4. 查看文件权限设置

### 性能问题
1. 调整 `MAX_CONCURRENT_REQUESTS`
2. 增加 `WORKER_CONNECTIONS`
3. 优化 `REQUEST_TIMEOUT`
4. 监控系统资源使用情况 
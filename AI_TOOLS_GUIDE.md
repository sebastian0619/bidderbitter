# AI工具系统使用指南

## 概述

本系统集成了强大的AI工具调用功能，让AI助手能够自动调用各种工具来帮助用户完成复杂的任务。系统基于[Docling](https://github.com/docling-project/docling)文档处理库，提供了网页读取、数据库操作、文档处理等核心功能。

## 核心功能

### 1. 网页读取工具

**功能描述**: 自动读取网页内容，提取文本、链接、表格等信息

**使用场景**:
- 从法律评级网站获取奖项信息
- 搜索律师事务所的最新动态
- 获取行业新闻和趋势

**示例用法**:
```javascript
// 读取钱伯斯网站
await tool_manager.execute_tool("read_webpage", {
  url: "https://chambers.com/legal-guide",
  timeout: 30
})
```

### 2. 数据库操作工具

**功能描述**: 直接执行SQL查询，获取数据库中的信息

**可用工具**:
- `get_awards_by_firm`: 根据律师事务所获取奖项
- `get_performances_by_firm`: 根据律师事务所获取业绩
- `search_similar_awards`: 搜索相似奖项
- `get_database_statistics`: 获取统计数据
- `execute_database_query`: 执行自定义SQL查询

**示例用法**:
```javascript
// 查询金杜律师事务所的奖项
await tool_manager.execute_tool("get_awards_by_firm", {
  law_firm: "金杜律师事务所",
  year: 2023
})
```

### 3. 文档处理工具（基于Docling）

**功能描述**: 使用Docling处理各种格式的文档，提取结构化信息

**支持格式**:
- PDF文档
- Word文档 (DOCX)
- Excel表格 (XLSX)
- HTML网页
- 图片文件

**示例用法**:
```javascript
// 处理文档并提取信息
await tool_manager.execute_tool("process_document", {
  file_path: "/app/uploads/document.pdf"
})
```

### 4. AI自动检索工具

**功能描述**: 在法律评级网站自动搜索奖项信息

**支持网站**:
- Chambers & Partners
- Legal 500
- IFLR1000

**示例用法**:
```javascript
// 搜索钱伯斯奖项
await tool_manager.execute_tool("search_legal_awards", {
  law_firm: "金杜律师事务所",
  year: 2023,
  source: "chambers"
})
```

## AI助手使用指南

### 基本使用

1. **访问AI助手页面**: 在侧边栏点击"AI智能助手"
2. **查看可用工具**: 展开"可用工具"面板查看所有可用功能
3. **输入问题**: 在输入框中描述您的需求
4. **自动工具调用**: AI会自动选择合适的工具来帮助您

### 快捷操作

系统提供了以下快捷操作按钮：

- 🔍 **搜索奖项**: 快速搜索律师事务所的获奖情况
- 📊 **查询业绩**: 查询律师事务所的业绩信息
- 📄 **分析文档**: 分析上传的文档并提取信息
- 📈 **数据统计**: 获取数据库统计信息
- 🌐 **网页搜索**: 搜索法律评级网站信息

### 对话示例

**用户**: "请帮我搜索金杜律师事务所在2023年的获奖情况"

**AI助手**: 
1. 自动调用 `search_legal_awards` 工具搜索钱伯斯网站
2. 自动调用 `get_awards_by_firm` 工具查询数据库
3. 整合结果并生成完整报告

**用户**: "请分析我上传的文档，提取其中的奖项信息"

**AI助手**:
1. 自动调用 `process_document` 工具处理文档
2. 使用AI分析提取的内容
3. 生成结构化的奖项信息

## 技术架构

### 后端架构

```
AI工具系统
├── ai_tools.py          # 工具定义和实现
├── ai_tools_api.py      # API接口
├── ai_service.py        # AI服务集成
└── main.py             # 主应用注册
```

### 工具管理器

```python
class AIToolManager:
    """AI工具管理器"""
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
```

### AI服务集成

```python
class AIService:
    """AI服务类"""
    
    async def chat_with_tools(
        self, 
        user_message: str, 
        system_prompt: str = "",
        tools: List[Dict[str, Any]] = None,
        tool_executor: Callable = None
    ) -> Dict[str, Any]:
        """支持工具调用的AI对话"""
```

## 配置说明

### 环境变量

```bash
# AI服务配置
AI_PROVIDER=openai                    # AI提供商 (openai/azure/custom)
OPENAI_API_KEY=your_api_key          # OpenAI API密钥
OPENAI_MODEL=gpt-4                   # 文本模型
OPENAI_VISION_MODEL=gpt-4-vision     # 视觉模型

# 数据库配置
DATABASE_URL=postgresql://...         # 数据库连接URL

# 文档处理配置
UPLOAD_DIR=/app/uploads              # 上传目录
GENERATED_DIR=/app/generated_docs    # 生成文档目录
```

### 工具配置

在 `ai_tools.py` 中可以配置：

- 网页读取超时时间
- 数据库连接参数
- 文档处理选项
- AI模型参数

## 扩展开发

### 添加新工具

1. 在 `ai_tools.py` 中定义新工具类
2. 在 `AIToolManager.get_tools()` 中注册工具
3. 在 `AIToolManager.execute_tool()` 中实现工具执行逻辑

**示例**:
```python
class NewTool:
    """新工具类"""
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具逻辑"""
        # 实现工具功能
        return {"success": True, "result": "工具执行结果"}

# 在AIToolManager中注册
async def get_tools(self) -> List[Dict[str, Any]]:
    tools = [
        # ... 现有工具
        {
            "name": "new_tool",
            "description": "新工具描述",
            "parameters": {
                "param1": {"type": "string", "description": "参数1"},
                "param2": {"type": "integer", "description": "参数2"}
            }
        }
    ]
    return tools
```

### 自定义AI提示词

可以在 `ai_tools_api.py` 中自定义系统提示词：

```python
system_prompt = f"""
你是一个专业的法律行业投标助手，拥有以下工具可以使用：

{json.dumps(tools, ensure_ascii=False, indent=2)}

使用规则：
1. 当用户询问需要获取外部信息时，优先使用工具
2. 当需要查询数据库信息时，使用相应的数据库工具
3. 当需要处理文档时，使用文档处理工具
4. 始终用中文回复用户

请根据用户的问题，选择合适的工具来帮助用户。
"""
```

## 故障排除

### 常见问题

1. **工具调用失败**
   - 检查网络连接
   - 验证API密钥配置
   - 查看错误日志

2. **文档处理失败**
   - 确认文件格式支持
   - 检查文件大小限制
   - 验证文件路径

3. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 确认数据库权限

### 日志查看

```bash
# 查看应用日志
docker logs bidderbitter-backend-1

# 查看AI工具日志
grep "AI工具" /var/log/app.log
```

### 性能优化

1. **工具缓存**: 对频繁调用的工具结果进行缓存
2. **并发控制**: 限制同时执行的工具数量
3. **超时设置**: 合理设置工具执行超时时间

## 安全注意事项

1. **API密钥安全**: 不要在代码中硬编码API密钥
2. **数据库安全**: 限制数据库工具的查询权限
3. **文件安全**: 验证上传文件的类型和大小
4. **网络安全**: 限制外部网站访问权限

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 集成Docling文档处理
- 支持网页读取和数据库操作
- 实现AI工具调用功能

## 技术支持

如有问题，请查看：
- [项目文档](./README.md)
- [高级功能说明](./ADVANCED_FEATURES.md)
- [API文档](./docs/api.md)

---

*本指南基于 [Docling](https://github.com/docling-project/docling) 文档处理库构建* 
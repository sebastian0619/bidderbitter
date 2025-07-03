from typing import Optional, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

# 尝试导入FastMCP，如果失败则记录警告
try:
    from fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    logger.warning("FastMCP未安装，MCP功能将不可用")
    MCP_AVAILABLE = False

class MCPSettings:
    """MCP服务器配置设置"""
    def __init__(self, server_url: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 30, enabled: bool = False):
        self.server_url = server_url
        self.api_key = api_key
        self.timeout = timeout
        self.enabled = enabled

class MCPClient:
    """MCP客户端，用于调用远程MCP服务器工具"""
    def __init__(self, settings: MCPSettings = None):
        self.settings = settings or MCPSettings()
        self.client = None
        self.initialized = False
        
        # 不再自动初始化，只在明确启用时才初始化

    def initialize(self):
        """初始化MCP客户端"""
        if not MCP_AVAILABLE:
            logger.error("FastMCP未安装，无法初始化MCP客户端")
            return False
            
        if not self.settings.enabled:
            logger.info("MCP客户端未启用，跳过初始化")
            return False
            
        if not self.settings.server_url:
            logger.error("MCP服务器URL未配置")
            return False
            
        try:
            # 修复FastMCP初始化参数
            self.client = FastMCP(
                name="BidderBitter-AI-Client"
                # 移除不支持的参数
            )
            
            # 设置连接参数
            if hasattr(self.client, 'connect'):
                self.client.connect(
                    server_url=self.settings.server_url,
                    timeout=self.settings.timeout
                )
            
            self.initialized = True
            logger.info(f"MCP客户端已连接到服务器: {self.settings.server_url}")
            return True
            
        except Exception as e:
            logger.error(f"MCP客户端初始化失败: {str(e)}")
            self.initialized = False
            return False

    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """调用MCP服务器上的工具"""
        if not MCP_AVAILABLE:
            return {
                "success": False,
                "error": "FastMCP未安装，MCP功能不可用"
            }
            
        if not self.initialized:
            if self.settings.enabled and self.settings.server_url:
                if not self.initialize():
                    return {
                        "success": False,
                        "error": "MCP客户端初始化失败"
                    }
            else:
                return {
                    "success": False,
                    "error": "MCP客户端未启用或未配置"
                }

        try:
            result = await self.client.call_tool(tool_name, **kwargs)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"调用MCP工具'{tool_name}'失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def is_available(self) -> bool:
        """检查MCP客户端是否可用"""
        return MCP_AVAILABLE and self.initialized
        
    def get_status(self) -> Dict[str, Any]:
        """获取MCP客户端状态"""
        return {
            "available": MCP_AVAILABLE,
            "enabled": self.settings.enabled,
            "initialized": self.initialized,
            "server_url": self.settings.server_url if self.settings.enabled else None
        }

# 创建全局MCP客户端实例（默认未启用）
mcp_client = MCPClient(MCPSettings(enabled=False))
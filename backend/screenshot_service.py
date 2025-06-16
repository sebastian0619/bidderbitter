import os
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import requests
import hashlib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScreenshotService:
    """网页截图服务"""
    
    def __init__(self, selenium_hub_url: str = "http://chrome:4444/wd/hub"):
        self.selenium_hub_url = selenium_hub_url
        self.screenshot_dir = "/app/screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def get_driver(self) -> webdriver.Remote:
        """获取Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = webdriver.Remote(
                command_executor=self.selenium_hub_url,
                options=chrome_options
            )
            # 设置页面加载超时
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            return driver
        except Exception as e:
            logger.error(f"创建WebDriver失败: {str(e)}")
            raise e
    
    async def capture_full_page_screenshot(self, url: str, award_id: int = None) -> Dict:
        """捕获完整页面截图"""
        driver = None
        try:
            start_time = time.time()
            
            # 生成文件名
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"award_{award_id}_{timestamp}_{url_hash}.png" if award_id else f"screenshot_{timestamp}_{url_hash}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            driver = self.get_driver()
            
            # 访问页面
            logger.info(f"正在访问页面: {url}")
            driver.get(url)
            
            # 等待页面加载
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待额外的资源加载
            time.sleep(3)
            
            # 滚动到页面底部以确保所有内容加载
            self._scroll_to_bottom(driver)
            
            # 获取页面总高度
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            # 如果页面高度小于等于视口高度，直接截图
            if total_height <= viewport_height:
                screenshot_data = driver.get_screenshot_as_png()
                with open(filepath, 'wb') as f:
                    f.write(screenshot_data)
                pages = [{"page": 1, "path": filepath}]
            else:
                # 分页截图
                pages = await self._capture_long_page(driver, filepath, total_height, viewport_height)
            
            processing_time = time.time() - start_time
            
            # 获取页面基本信息
            page_info = self._get_page_info(driver)
            
            return {
                "success": True,
                "url": url,
                "pages": pages,
                "total_pages": len(pages),
                "page_info": page_info,
                "processing_time": processing_time,
                "total_height": total_height
            }
            
        except Exception as e:
            logger.error(f"网页截图失败: {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "processing_time": time.time() - start_time if 'start_time' in locals() else 0
            }
        finally:
            if driver:
                driver.quit()
    
    async def _capture_long_page(self, driver: webdriver.Remote, base_filepath: str, total_height: int, viewport_height: int) -> List[Dict]:
        """捕获长页面，分页截图"""
        pages = []
        current_position = 0
        page_number = 1
        
        # 设置合适的页面高度（A4纸比例）
        page_height = min(viewport_height, 1400)  # 限制单页高度
        
        while current_position < total_height:
            # 滚动到指定位置
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(1)  # 等待滚动完成
            
            # 生成页面文件名
            filename = base_filepath.replace('.png', f'_page_{page_number}.png')
            
            # 截图
            screenshot_data = driver.get_screenshot_as_png()
            with open(filename, 'wb') as f:
                f.write(screenshot_data)
            
            pages.append({
                "page": page_number,
                "path": filename,
                "start_position": current_position,
                "end_position": min(current_position + page_height, total_height)
            })
            
            current_position += page_height
            page_number += 1
            
            # 防止无限循环
            if page_number > 20:  # 最多20页
                logger.warning(f"页面过长，已截取前20页")
                break
        
        return pages
    
    def _scroll_to_bottom(self, driver: webdriver.Remote):
        """滚动到页面底部"""
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # 滚动到底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 等待加载
            time.sleep(2)
            
            # 计算新的高度
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
            last_height = new_height
    
    def _get_page_info(self, driver: webdriver.Remote) -> Dict:
        """获取页面基本信息"""
        try:
            return {
                "title": driver.title,
                "url": driver.current_url,
                "viewport_size": driver.get_window_size(),
                "page_source_length": len(driver.page_source)
            }
        except Exception as e:
            logger.error(f"获取页面信息失败: {str(e)}")
            return {}
    
    async def capture_award_pages(self, urls: List[str], award_id: int) -> Dict:
        """批量捕获获奖页面"""
        results = []
        
        for i, url in enumerate(urls):
            logger.info(f"正在处理第 {i+1}/{len(urls)} 个URL: {url}")
            
            try:
                result = await self.capture_full_page_screenshot(url, award_id)
                results.append(result)
                
                # 添加延迟避免被反爬
                if i < len(urls) - 1:
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"处理URL失败 {url}: {str(e)}")
                results.append({
                    "success": False,
                    "url": url,
                    "error": str(e)
                })
        
        return {
            "total_urls": len(urls),
            "successful": len([r for r in results if r.get("success", False)]),
            "failed": len([r for r in results if not r.get("success", False)]),
            "results": results
        }
    
    def optimize_screenshot_for_word(self, image_path: str, max_width: int = 1654) -> str:
        """优化截图以适应Word文档（A4纸宽度）"""
        try:
            # A4纸在Word中的像素宽度约为1654px (210mm * 96dpi / 25.4)
            with Image.open(image_path) as img:
                original_width, original_height = img.size
                
                if original_width > max_width:
                    # 计算缩放比例
                    scale_ratio = max_width / original_width
                    new_height = int(original_height * scale_ratio)
                    
                    # 重新调整大小
                    resized_img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 生成新文件名
                    optimized_path = image_path.replace('.png', '_optimized.png')
                    resized_img.save(optimized_path, 'PNG', optimize=True)
                    
                    return optimized_path
                else:
                    return image_path
                    
        except Exception as e:
            logger.error(f"优化截图失败: {str(e)}")
            return image_path

# 创建全局截图服务实例
screenshot_service = ScreenshotService() 
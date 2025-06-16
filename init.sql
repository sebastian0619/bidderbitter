-- 创建数据库初始化脚本
-- 这个文件将在PostgreSQL容器启动时自动执行

-- 创建数据库（如果不存在）
-- CREATE DATABASE IF NOT EXISTS bidder_db;

-- 设置默认字符集
ALTER DATABASE bidder_db SET default_text_search_config = 'pg_catalog.simple';

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 插入初始厂牌数据
-- 这些数据将由应用启动时的Python代码插入，这里只做参考

/*
INSERT INTO brands (name, full_name, website, is_active, created_at) VALUES
('Chambers', 'Chambers and Partners', 'https://chambers.com', true, NOW()),
('Legal Band', 'Legal Band', 'https://legalband.com', true, NOW()),
('ALB', 'Asian Legal Business', 'https://www.legalbusinessonline.com', true, NOW()),
('IFLR', 'International Financial Law Review', 'https://www.iflr.com', true, NOW())
ON CONFLICT (name) DO NOTHING;

INSERT INTO business_fields (name, is_active, created_at) VALUES
('银行与金融', true, NOW()),
('资本市场', true, NOW()),
('并购重组', true, NOW()),
('公司业务', true, NOW()),
('争议解决', true, NOW()),
('知识产权', true, NOW()),
('劳动法', true, NOW()),
('税法', true, NOW()),
('房地产', true, NOW()),
('建设工程', true, NOW()),
('环境法', true, NOW()),
('能源法', true, NOW()),
('航运海事', true, NOW()),
('国际贸易', true, NOW()),
('合规', true, NOW())
ON CONFLICT (name) DO NOTHING;
*/ 
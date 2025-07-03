-- 创建数据库初始化脚本
-- 这个文件将在PostgreSQL容器启动时自动执行

-- 创建数据库（如果不存在）
-- CREATE DATABASE IF NOT EXISTS bidder_db;

-- 设置默认字符集
ALTER DATABASE bidder_db SET default_text_search_config = 'pg_catalog.simple';

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建律师证表（如果不存在）
-- 这个表用于存储律师执业证书信息
CREATE TABLE IF NOT EXISTS lawyer_certificates (
    id SERIAL PRIMARY KEY,
    lawyer_name VARCHAR(100) NOT NULL,
    certificate_number VARCHAR(100) NOT NULL UNIQUE,
    law_firm VARCHAR(300) NOT NULL,
    issuing_authority VARCHAR(200),
    age INTEGER,
    id_number VARCHAR(20),
    issue_date TIMESTAMP,
    position VARCHAR(50),
    position_tags JSON DEFAULT '[]',
    business_field_tags JSON DEFAULT '[]',
    custom_tags JSON DEFAULT '[]',
    source_document VARCHAR(500),
    ai_analysis JSON,
    confidence_score FLOAT,
    extracted_text TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    is_manual_input BOOLEAN DEFAULT FALSE,
    verification_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建律师证文件表（如果不存在）
CREATE TABLE IF NOT EXISTS lawyer_certificate_files (
    id SERIAL PRIMARY KEY,
    certificate_id INTEGER REFERENCES lawyer_certificates(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_name VARCHAR(255),
    file_size INTEGER,
    page_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建律师证相关索引
CREATE INDEX IF NOT EXISTS idx_lawyer_certificates_name ON lawyer_certificates(lawyer_name);
CREATE INDEX IF NOT EXISTS idx_lawyer_certificates_cert_num ON lawyer_certificates(certificate_number);
CREATE INDEX IF NOT EXISTS idx_lawyer_certificates_law_firm ON lawyer_certificates(law_firm);
CREATE INDEX IF NOT EXISTS idx_lawyer_certificate_files_cert_id ON lawyer_certificate_files(certificate_id);

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
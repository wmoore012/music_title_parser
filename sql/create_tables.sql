-- SPDX-License-Identifier: MIT
-- Copyright (c) 2024 MusicScope

-- Music Title Parser Module Tables
-- Module-specific tables for version mappings and policy management

-- Version mapping table (replaces complex rules with simple key-value)
CREATE TABLE IF NOT EXISTS parser_version_mappings (
    mapping_id VARCHAR(100) PRIMARY KEY,
    input_pattern VARCHAR(200) NOT NULL,
    output_version VARCHAR(100) NOT NULL,
    mapping_type ENUM('single', 'combination', 'regex') NOT NULL DEFAULT 'single',
    priority INT NOT NULL DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_by VARCHAR(100) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_input_pattern (input_pattern),
    INDEX idx_mapping_type (mapping_type),
    INDEX idx_priority_active (priority, is_active)
) ENGINE=InnoDB COMMENT='Version mapping rules for title parsing';

-- Policy configurations table
CREATE TABLE IF NOT EXISTS parser_policy_configs (
    config_id VARCHAR(100) PRIMARY KEY,
    policy_name VARCHAR(200) NOT NULL,
    profile_name ENUM('strict', 'balanced', 'aggressive') NOT NULL,
    accept_min DECIMAL(3,2) NOT NULL,
    gray_min DECIMAL(3,2) NOT NULL,
    reject_below DECIMAL(3,2) NOT NULL,
    oac_boost DECIMAL(3,2) DEFAULT 0.15,
    use_channel_for_artist BOOLEAN DEFAULT FALSE,
    allow_stage_b BOOLEAN DEFAULT TRUE,
    shadow_only BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    version VARCHAR(20) DEFAULT '1.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_policy_profile (policy_name, profile_name),
    INDEX idx_profile_active (profile_name, is_active)
) ENGINE=InnoDB COMMENT='Parser policy configurations';

-- Allowlist entries table
CREATE TABLE IF NOT EXISTS parser_allowlist (
    entry_id VARCHAR(100) PRIMARY KEY,
    channel_name VARCHAR(300) NOT NULL,
    artist_name VARCHAR(300) NOT NULL,
    entry_type VARCHAR(50) NOT NULL DEFAULT 'youtube_oac',
    confidence_boost DECIMAL(3,2) DEFAULT 0.15,
    owner VARCHAR(100) NOT NULL,
    expires_at DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_channel_name (channel_name),
    INDEX idx_artist_name (artist_name),
    INDEX idx_entry_type (entry_type),
    INDEX idx_expires_active (expires_at, is_active)
) ENGINE=InnoDB COMMENT='Trusted channel to artist mappings';

-- Denylist entries table
CREATE TABLE IF NOT EXISTS parser_denylist (
    entry_id VARCHAR(100) PRIMARY KEY,
    pattern_text VARCHAR(500) NOT NULL,
    pattern_type ENUM('exact_match', 'regex', 'contains') NOT NULL DEFAULT 'exact_match',
    entry_type VARCHAR(50) NOT NULL DEFAULT 'garbage_pattern',
    action VARCHAR(20) DEFAULT 'reject',
    owner VARCHAR(100) NOT NULL,
    expires_at DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_pattern_type (pattern_type),
    INDEX idx_entry_type (entry_type),
    INDEX idx_expires_active (expires_at, is_active)
) ENGINE=InnoDB COMMENT='Garbage patterns and blocked content';

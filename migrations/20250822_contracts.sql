-- Create contracts table (for metadata and state)
-- MySQL-compatible
CREATE TABLE IF NOT EXISTS contracts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  prescriptor_id BIGINT UNSIGNED NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  sha256 CHAR(64) NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'generated',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_contracts_prescriptor (prescriptor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

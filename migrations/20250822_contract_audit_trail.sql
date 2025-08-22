-- Create contract_audit_trail table to record events
-- MySQL 8+ (JSON supported)
CREATE TABLE IF NOT EXISTS contract_audit_trail (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  prescriptor_id BIGINT UNSIGNED NOT NULL,
  event VARCHAR(100) NOT NULL,
  meta JSON NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_audit_prescriptor (prescriptor_id),
  KEY idx_audit_event (event)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

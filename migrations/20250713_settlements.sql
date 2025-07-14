-- Migración: soporte completo a rendición de facturas prescriptores
-- Autor: cascade
-- Fecha: 2025-07-13

-- 1) Invoice: columnas para fecha de pago, archivo de comprobante y monto pagado
ALTER TABLE invoice
    ADD COLUMN IF NOT EXISTS paid_at DATETIME NULL AFTER invoice_date,
    ADD COLUMN IF NOT EXISTS receipt_path VARCHAR(255) NULL AFTER paid_at,
    ADD COLUMN IF NOT EXISTS paid_amount DECIMAL(12,2) NULL AFTER receipt_path;

-- 2) Ledger: estado por defecto Pend. Rendición (id 3) y FK segura
ALTER TABLE ledger
    MODIFY COLUMN state_id TINYINT NOT NULL DEFAULT 3;

-- 3) Catálogo de estados de ledger: insertar RENDIDO (id 4) si no existe
INSERT INTO state_ledger (id, code, name)
SELECT 4, 'RENDIDO', 'Rendido'
WHERE NOT EXISTS (SELECT 1 FROM state_ledger WHERE id = 4);

-- 4) Índice para lead_history
ALTER TABLE lead_history
    ADD INDEX IF NOT EXISTS idx_lead_ts (lead_id, ts);


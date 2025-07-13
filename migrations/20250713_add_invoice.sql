-- Script: 20250713_add_invoice.sql
-- Objetivo: crear tabla invoice y enlazarla con ledger; agregar nuevo estado FACTURADO (id=7)

-- 1. Tabla invoice
CREATE TABLE IF NOT EXISTS invoice (
    id VARCHAR(36) PRIMARY KEY,
    prescriptor_id VARCHAR(36) NOT NULL,
    number VARCHAR(50) NOT NULL,
    invoice_date DATE NOT NULL,
    total DECIMAL(12,2) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_invoice_presc FOREIGN KEY (prescriptor_id) REFERENCES prescriptors(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Columna invoice_id en ledger (puede ser NULL hasta que se facture)
ALTER TABLE ledger
    ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36),
    ADD CONSTRAINT fk_ledger_invoice FOREIGN KEY (invoice_id) REFERENCES invoice(id) ON DELETE SET NULL;

-- 3. (Estado FACTURADO ya existe, id 3)

-- 4. Actualizar comment opcional
-- comentario descriptivo (MySQL comment)
ALTER TABLE invoice COMMENT = 'Facturas subidas por prescriptores';

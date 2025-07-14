-- Añade columna paid_amount para registrar importe efectivamente pagado al prescriptor
ALTER TABLE invoice
    ADD COLUMN paid_amount DECIMAL(10,2) NULL AFTER receipt_path;

-- Script: 20250830_add_prescriptor_document_fields.sql
-- Objetivo: agregar campos de documento y domicilio al prescriptor

-- MySQL 8.0+
ALTER TABLE prescriptors
    ADD COLUMN IF NOT EXISTS document_type VARCHAR(20) NULL AFTER squeeze_page_name,
    ADD COLUMN IF NOT EXISTS document_number VARCHAR(50) NULL AFTER document_type,
    ADD COLUMN IF NOT EXISTS domicile VARCHAR(255) NULL AFTER document_number;

-- Opcional: comentario de tabla/columnas
ALTER TABLE prescriptors COMMENT = 'Prescriptores con datos de identificación y domicilio';

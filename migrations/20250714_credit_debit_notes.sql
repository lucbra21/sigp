-- Migración: tablas de notas de crédito y débito para ajustes de prescriptores
-- Autor: cascade
-- Fecha: 2025-07-14

-- Tabla de notas de crédito
CREATE TABLE IF NOT EXISTS `credit_notes` (
  `id` char(36) NOT NULL,
  `prescriptor_id` char(36) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `note_date` date NOT NULL,
  `concept` varchar(150) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `fk_cn_pres` (`prescriptor_id`),
  CONSTRAINT `fk_cn_pres` FOREIGN KEY (`prescriptor_id`) REFERENCES `prescriptors` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Tabla de notas de débito
CREATE TABLE IF NOT EXISTS `debit_notes` (
  `id` char(36) NOT NULL,
  `prescriptor_id` char(36) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `note_date` date NOT NULL,
  `concept` varchar(150) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `fk_dn_pres` (`prescriptor_id`),
  CONSTRAINT `fk_dn_pres` FOREIGN KEY (`prescriptor_id`) REFERENCES `prescriptors` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- =============================================================================
-- Migración 001: conversaciones por usuario y metadatos RAG en los mensajes.
-- Aplica sobre una base creada con el schema.sql ANTERIOR (servidor actual).
-- Hacer un respaldo antes de ejecutar:  mysqldump <db> > respaldo.sql
-- =============================================================================

-- 1. Conversaciones: dueño y título
ALTER TABLE `conversations`
  ADD COLUMN `user_id` INT NULL AFTER `id`,
  ADD COLUMN `title` VARCHAR(100) NULL AFTER `user_id`,
  ADD COLUMN `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

UPDATE `conversations` SET `title` = `name`;

-- La conversación compartida anterior pasa a ser del primer administrador
UPDATE `conversations` SET `user_id` = (SELECT MIN(`id`) FROM `users` WHERE `role_id` = 1)
WHERE `user_id` IS NULL;

ALTER TABLE `conversations`
  DROP COLUMN `name`,
  MODIFY `user_id` INT NOT NULL,
  ADD CONSTRAINT `fk_conversations_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  ADD INDEX `idx_conversations_user` (`user_id`, `updated_at`);

-- 2. Mensajes: rol explícito (sin el usuario "999") y metadatos del motor RAG
ALTER TABLE `messages`
  ADD COLUMN `role` ENUM('user', 'assistant') NOT NULL DEFAULT 'user' AFTER `conversation_id`,
  ADD COLUMN `topic` VARCHAR(50) NULL AFTER `content`,
  ADD COLUMN `in_domain` TINYINT(1) NULL AFTER `topic`,
  ADD COLUMN `refused` VARCHAR(20) NULL AFTER `in_domain`,
  ADD COLUMN `sources` JSON NULL AFTER `refused`,
  ADD COLUMN `model` VARCHAR(100) NULL AFTER `sources`,
  ADD COLUMN `latency_ms` INT NULL AFTER `model`;

-- sender_id deja de ser obligatorio: las respuestas del asistente no tienen remitente
SET @fk := (SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'messages'
              AND COLUMN_NAME = 'sender_id' AND REFERENCED_TABLE_NAME = 'users' LIMIT 1);
SET @sql := CONCAT('ALTER TABLE `messages` DROP FOREIGN KEY `', @fk, '`');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

ALTER TABLE `messages` MODIFY `sender_id` INT NULL;

-- Mensajes del bot guardados con sender_id = 999 (o sin usuario existente)
UPDATE `messages` SET `role` = 'assistant', `sender_id` = NULL
WHERE `sender_id` = 999 OR `sender_id` NOT IN (SELECT `id` FROM `users`);

ALTER TABLE `messages`
  ADD CONSTRAINT `fk_messages_sender` FOREIGN KEY (`sender_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  ADD INDEX `idx_messages_conversation` (`conversation_id`, `id`),
  ADD INDEX `idx_messages_role_topic` (`role`, `topic`);

-- 3. Tablas con datos simulados que ya no se usan (el corpus lo reporta el
--    motor de IA y los temas se calculan a partir de las consultas reales)
DROP TABLE IF EXISTS `topics`;
DROP TABLE IF EXISTS `documents`;

-- 4. (Opcional) Si existía un usuario ficticio para el bot (id 999), ya no se
--    necesita: sus mensajes quedaron como role = 'assistant'.
-- DELETE FROM `users` WHERE `id` = 999;

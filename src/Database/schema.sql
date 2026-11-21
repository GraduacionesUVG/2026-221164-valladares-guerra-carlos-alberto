CREATE TABLE `roles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL UNIQUE,
  `password` VARCHAR(255) NOT NULL,
  `role_id` INT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Cada conversación pertenece a un único usuario
CREATE TABLE `conversations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `title` VARCHAR(100) NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_conversations_user` (`user_id`, `updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- role = 'user' (consulta del ciudadano) o 'assistant' (respuesta de VialBot).
-- En las consultas se registran el tema y el dominio que asigna el clasificador
-- (análisis de patrones, objetivo específico 3); en las respuestas, las fuentes
-- citadas, el modelo que respondió y la latencia.
CREATE TABLE `messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `conversation_id` INT NOT NULL,
  `role` ENUM('user', 'assistant') NOT NULL,
  `sender_id` INT NULL,
  `content` TEXT NOT NULL,
  `topic` VARCHAR(50) NULL,
  `in_domain` TINYINT(1) NULL,
  `refused` VARCHAR(20) NULL,
  `sources` JSON NULL,
  `model` VARCHAR(100) NULL,
  `latency_ms` INT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`conversation_id`) REFERENCES `conversations`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`sender_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_messages_conversation` (`conversation_id`, `id`),
  INDEX `idx_messages_role_topic` (`role`, `topic`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

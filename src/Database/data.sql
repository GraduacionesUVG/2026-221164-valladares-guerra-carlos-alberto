-- Roles
INSERT INTO `roles` (`id`, `name`) VALUES (1, 'Admin'), (2, 'User');

-- Usuarios de desarrollo (contraseña: 'password'). Cambiarlas en producción.
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role_id`) VALUES
(1, 'Admin User', 'admin@example.com', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 1),
(2, 'Test User', 'user@example.com', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 2);

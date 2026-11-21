<?php
/**
 * Configuración de la aplicación.
 *
 * Los valores se leen de variables de entorno. En servidores donde no es posible
 * definirlas (ej. hosting compartido), se puede crear config/local.php con un
 * arreglo que sobrescriba estas llaves. Ese archivo está en .gitignore y NUNCA
 * debe subirse al repositorio.
 */
$local = file_exists(__DIR__ . '/local.php') ? require __DIR__ . '/local.php' : [];

$env = function (string $key, $default = null) use ($local) {
    if (array_key_exists($key, $local)) {
        return $local[$key];
    }
    $value = getenv($key);
    return $value === false ? $default : $value;
};

return [
    'env' => $env('APP_ENV', 'production'),
    // Secreto para firmar los JWT. Obligatorio fuera del entorno local.
    'jwt_secret' => $env('JWT_SECRET'),
    'jwt_ttl' => (int) $env('JWT_TTL', 60 * 60 * 8),
    // Orígenes permitidos para CORS (separados por coma). En producción el
    // frontend y la API comparten dominio, por lo que no se necesita CORS.
    'cors_origins' => array_filter(array_map('trim', explode(',', (string) $env('CORS_ORIGINS', 'http://localhost:5173')))),
    // Motor de IA (servicio Python en AI/)
    'ai_service_url' => rtrim((string) $env('AI_SERVICE_URL', 'http://localhost:8000'), '/'),
    'ai_service_token' => $env('AI_SERVICE_TOKEN', ''),
    'ai_timeout' => (int) $env('AI_TIMEOUT', 120),
];

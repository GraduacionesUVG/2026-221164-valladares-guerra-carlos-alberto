<?php
/**
 * Copiar como config/local.php en el servidor y completar los valores.
 * config/local.php está en .gitignore: nunca lo subas al repositorio.
 */
return [
    'APP_ENV' => 'production',
    // Genera uno con: php -r "echo bin2hex(random_bytes(32));"
    'JWT_SECRET' => '',
    'CORS_ORIGINS' => 'https://cvguerra.nubix.gt',

    'DB_HOST' => 'localhost',
    'DB_NAME' => '',
    'DB_USER' => '',
    'DB_PASS' => '',

    // URL del servicio de IA (carpeta AI/) y token compartido con él
    'AI_SERVICE_URL' => 'http://127.0.0.1:8000',
    'AI_SERVICE_TOKEN' => '',
];

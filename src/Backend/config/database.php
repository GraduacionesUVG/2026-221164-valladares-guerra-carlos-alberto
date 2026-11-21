<?php
// Mismo mecanismo que config/app.php: variables de entorno o config/local.php
$local = file_exists(__DIR__ . '/local.php') ? require __DIR__ . '/local.php' : [];
$env = function (string $key, $default) use ($local) {
    if (array_key_exists($key, $local)) {
        return $local[$key];
    }
    $value = getenv($key);
    return $value === false ? $default : $value;
};

return [
    'host' => $env('DB_HOST', 'db'),
    'dbname' => $env('DB_NAME', 'trabajograduacion'),
    'username' => $env('DB_USER', 'root'),
    'password' => $env('DB_PASS', 'root'),
    'charset' => $env('DB_CHARSET', 'utf8mb4'),
    'options' => [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]
];

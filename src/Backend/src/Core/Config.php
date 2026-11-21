<?php
namespace App\Core;

class Config
{
    private static $config = null;

    public static function get(string $key, $default = null)
    {
        if (self::$config === null) {
            self::$config = require __DIR__ . '/../../config/app.php';
        }
        return self::$config[$key] ?? $default;
    }
}

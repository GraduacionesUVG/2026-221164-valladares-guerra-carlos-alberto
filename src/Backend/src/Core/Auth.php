<?php
namespace App\Core;

/**
 * Usuario autenticado de la petición actual. El Router lo establece a partir
 * del JWT validado, de modo que los controladores nunca confían en un id de
 * usuario enviado por el cliente.
 */
class Auth
{
    private static $payload = null;

    public static function setPayload(array $payload): void
    {
        self::$payload = $payload;
    }

    public static function id(): ?int
    {
        return isset(self::$payload['id']) ? (int) self::$payload['id'] : null;
    }

    public static function role(): ?string
    {
        return self::$payload['role'] ?? null;
    }

    public static function isAdmin(): bool
    {
        return self::role() === 'Admin';
    }
}

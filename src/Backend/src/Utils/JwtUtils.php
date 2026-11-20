<?php
namespace App\Utils;

use App\Core\Config;
use RuntimeException;

class JwtUtils
{
    private const DEV_SECRET = 'dev-only-secret-do-not-use-in-production';

    private static function secret(): string
    {
        $secret = Config::get('jwt_secret');
        if (!empty($secret)) {
            return $secret;
        }
        if (Config::get('env') === 'local') {
            return self::DEV_SECRET;
        }
        throw new RuntimeException('JWT_SECRET no está configurado');
    }

    public static function generate(array $payload): string
    {
        $now = time();
        $payload['iat'] = $now;
        $payload['exp'] = $now + Config::get('jwt_ttl', 28800);

        $header = self::base64UrlEncode(json_encode(['typ' => 'JWT', 'alg' => 'HS256']));
        $body = self::base64UrlEncode(json_encode($payload));
        $signature = self::base64UrlEncode(hash_hmac('sha256', "$header.$body", self::secret(), true));

        return "$header.$body.$signature";
    }

    /**
     * Devuelve el payload si la firma es válida y el token no ha expirado.
     */
    public static function validate(string $token)
    {
        $parts = explode('.', $token);
        if (count($parts) !== 3) {
            return false;
        }

        [$header, $body, $signature] = $parts;
        $expected = self::base64UrlEncode(hash_hmac('sha256', "$header.$body", self::secret(), true));

        // Comparación en tiempo constante para evitar ataques de temporización
        if (!hash_equals($expected, $signature)) {
            return false;
        }

        $payload = json_decode(self::base64UrlDecode($body), true);
        if (!is_array($payload) || !isset($payload['exp']) || $payload['exp'] < time()) {
            return false;
        }
        return $payload;
    }

    private static function base64UrlEncode($data): string
    {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }

    private static function base64UrlDecode($data)
    {
        return base64_decode(strtr($data, '-_', '+/'));
    }
}

<?php
namespace App\Services\Ai;

use App\Core\Config;

/**
 * Cliente HTTP del motor de IA (servicio Python/FastAPI de la carpeta AI/).
 * El backend PHP actúa como gateway: autentica al usuario, guarda el historial
 * y delega la recuperación y generación a este servicio.
 */
class AiServiceClient
{
    private $baseUrl;
    private $token;
    private $timeout;

    public function __construct()
    {
        $this->baseUrl = Config::get('ai_service_url');
        $this->token = Config::get('ai_service_token');
        $this->timeout = Config::get('ai_timeout', 120);
    }

    public function query(string $question, array $history = []): array
    {
        return $this->request('POST', '/query', ['question' => $question, 'history' => $history]);
    }

    public function retrieve(string $question, int $topK = 4): array
    {
        return $this->request('POST', '/retrieve', ['question' => $question, 'top_k' => $topK]);
    }

    public function health(): array
    {
        return $this->request('GET', '/health', null, 5);
    }

    public function corpus(): array
    {
        return $this->request('GET', '/corpus', null, 10);
    }

    public function config(): array
    {
        return $this->request('GET', '/config', null, 10);
    }

    public function metrics(): array
    {
        return $this->request('GET', '/metrics', null, 10);
    }

    public function logs(?string $source = null, int $limit = 50): array
    {
        $qs = http_build_query(array_filter(['source' => $source, 'limit' => $limit]));
        return $this->request('GET', '/logs?' . $qs, null, 5);
    }

    public function getSettings(): array
    {
        return $this->request('GET', '/settings', null, 10);
    }

    /** $patch: solo los campos que se quieren cambiar, o ['reset' => true]. */
    public function updateSettings(array $patch): array
    {
        return $this->request('PUT', '/settings', $patch, 10);
    }

    private function request(string $method, string $path, ?array $body = null, ?int $timeout = null): array
    {
        $ch = curl_init($this->baseUrl . $path);
        $headers = ['Accept: application/json'];
        if (!empty($this->token)) {
            $headers[] = 'X-Internal-Token: ' . $this->token;
        }
        if ($body !== null) {
            $headers[] = 'Content-Type: application/json';
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body));
        }
        curl_setopt_array($ch, [
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_CONNECTTIMEOUT => 3,
            CURLOPT_TIMEOUT => $timeout ?? $this->timeout,
        ]);

        $response = curl_exec($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($response === false) {
            throw new AiServiceException("Motor de IA no disponible: $error");
        }
        $data = json_decode($response, true);
        if ($status >= 400 || !is_array($data)) {
            $detail = is_array($data) ? ($data['detail'] ?? 'error') : 'respuesta inválida';
            throw new AiServiceException("Motor de IA respondió $status: " . (is_string($detail) ? $detail : json_encode($detail)));
        }
        return $data;
    }
}

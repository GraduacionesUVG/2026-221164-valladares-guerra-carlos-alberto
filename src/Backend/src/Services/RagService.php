<?php

namespace App\Services;

use App\Services\Ai\AiServiceClient;
use App\Services\Ai\AiServiceException;

/**
 * Orquesta la consulta al motor RAG y normaliza su respuesta para el resto
 * del backend. Si el motor no está disponible, devuelve una respuesta de
 * error controlada en lugar de inventar una.
 */
class RagService
{
    public const UNAVAILABLE_MESSAGE =
        'El asistente no está disponible en este momento. Por favor, intenta de nuevo en unos minutos.';

    private $client;

    public function __construct(?AiServiceClient $client = null)
    {
        $this->client = $client ?? new AiServiceClient();
    }

    /**
     * @param array $history Turnos previos [['role' => 'user'|'assistant', 'content' => '...']]
     */
    public function answerQuery(string $userQuery, array $history = []): array
    {
        try {
            $result = $this->client->query($userQuery, $history);
        } catch (AiServiceException $e) {
            error_log('[RagService] ' . $e->getMessage());
            return [
                'answer' => self::UNAVAILABLE_MESSAGE,
                'available' => false,
                'topic' => null,
                'in_domain' => null,
                'refused' => 'unavailable',
                'model' => null,
                'latency_ms' => null,
                'sources' => [],
            ];
        }

        return [
            'answer' => $result['answer'],
            'available' => true,
            'topic' => $result['topic'] ?? null,
            'in_domain' => $result['in_domain'] ?? null,
            'refused' => $result['refused'] ?? null,
            'model' => $result['model'] ?? null,
            'latency_ms' => $result['latency_ms']['total'] ?? null,
            // Al cliente solo se envían la referencia, el título y la similitud
            'sources' => array_map(fn($s) => [
                'reference' => $s['reference'],
                'heading' => $s['heading'],
                'score' => $s['score'],
            ], $result['sources'] ?? []),
        ];
    }
}

<?php

namespace App\Controllers;

use App\Attributes\Route;
use App\Attributes\Authorize;
use App\DTOs\Chat\SendMessageRequest;
use App\Services\Ai\AiServiceClient;
use App\Services\Ai\AiServiceException;
use App\Utils\Response;

/**
 * Endpoints de administración del motor RAG: configuración activa, métricas de
 * evaluación y playground para auditar el contexto recuperado.
 */
class RagController
{
    private $client;

    public function __construct()
    {
        $this->client = new AiServiceClient();
    }

    #[Route('/rag/config', 'GET')]
    #[Authorize(['Admin'])]
    public function config()
    {
        $this->proxy(fn() => $this->client->config());
    }

    #[Route('/rag/metrics', 'GET')]
    #[Authorize(['Admin'])]
    public function metrics()
    {
        $this->proxy(fn() => $this->client->metrics());
    }

    /** Parámetros ajustables en caliente (Top K, umbrales, temperatura, prompt). */
    #[Route('/rag/settings', 'GET')]
    #[Authorize(['Admin'])]
    public function getSettings()
    {
        $this->proxy(fn() => $this->client->getSettings());
    }

    #[Route('/rag/settings', 'PUT')]
    #[Authorize(['Admin'])]
    public function updateSettings()
    {
        $data = json_decode(file_get_contents('php://input'), true) ?? [];

        if (!empty($data['reset'])) {
            $this->proxy(fn() => $this->client->updateSettings(['reset' => true]));
            return;
        }

        $allowed = ['top_k', 'min_retrieval_score', 'in_domain_threshold',
                   'temperature', 'prefer_finetuned_generator', 'system_prompt'];
        $patch = array_intersect_key($data, array_flip($allowed));

        $ranges = ['top_k' => [1, 10], 'min_retrieval_score' => [0, 1],
                  'in_domain_threshold' => [0, 1], 'temperature' => [0, 1]];
        foreach ($ranges as $key => [$min, $max]) {
            if (isset($patch[$key]) && (!is_numeric($patch[$key]) || $patch[$key] < $min || $patch[$key] > $max)) {
                Response::error("$key debe estar entre $min y $max", 400);
            }
        }
        if (isset($patch['system_prompt']) && mb_strlen((string) $patch['system_prompt']) > 4000) {
            Response::error('system_prompt no debe exceder 4000 caracteres', 400);
        }
        if (empty($patch)) {
            Response::error('No se envió ningún campo válido para actualizar', 400);
        }

        $this->proxy(fn() => $this->client->updateSettings($patch));
    }

    /** Consulta completa sin guardar en el historial; devuelve el contexto crudo. */
    #[Route('/rag/playground', 'POST')]
    #[Authorize(['Admin'])]
    public function playground()
    {
        $request = new SendMessageRequest(json_decode(file_get_contents('php://input'), true));
        if (!$request->validate()) {
            Response::error('content is required', 400);
        }
        $this->proxy(fn() => $this->client->query($request->content));
    }

    private function proxy(callable $call)
    {
        try {
            Response::json($call());
        } catch (AiServiceException $e) {
            error_log('[RagController] ' . $e->getMessage());
            Response::error('Motor de IA no disponible', 503);
        }
    }
}

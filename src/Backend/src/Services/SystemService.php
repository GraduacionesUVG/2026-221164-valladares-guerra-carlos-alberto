<?php

namespace App\Services;

use App\Repositories\LogRepository;
use App\Services\Ai\AiServiceClient;
use App\Services\Ai\AiServiceException;
use App\Utils\Database;
use Throwable;

/**
 * Estado real de cada componente de la arquitectura. Las latencias se miden
 * en el momento de la consulta; no hay valores simulados.
 */
class SystemService
{
    private $aiClient;

    public function __construct()
    {
        $this->aiClient = new AiServiceClient();
    }

    private static function ms(float $start): string
    {
        return round((microtime(true) - $start) * 1000) . 'ms';
    }

    public function getSystemHealth(): array
    {
        $requestStart = $_SERVER['REQUEST_TIME_FLOAT'] ?? microtime(true);

        $t = microtime(true);
        try {
            Database::getInstance()->getConnection()->query('SELECT 1');
            $database = ['status' => 'healthy', 'latency' => self::ms($t), 'label' => 'Conectada'];
        } catch (Throwable $e) {
            $database = ['status' => 'offline', 'latency' => '-', 'label' => 'Desconectada'];
        }

        $t = microtime(true);
        try {
            $ai = $this->aiClient->health();
            $aiLatency = self::ms($t);
            $aiNode = ['status' => $ai['status'] === 'healthy' ? 'healthy' : 'warning',
                       'latency' => $aiLatency, 'label' => $ai['status'] === 'healthy' ? 'Online' : 'Degradado'];
            $vectordb = [
                'status' => $ai['vectordb']['status'],
                'latency' => $ai['vectordb']['vectors'] . ' vectores',
                'label' => 'Indexado',
                'detail' => 'ChromaDB • ' . $ai['embedder']['model'] . ($ai['embedder']['finetuned'] ? ' (propio)' : ' (base)'),
            ];
            $llm = [
                'status' => $ai['llm']['status'] === 'healthy' && $ai['llm']['available'] ? 'healthy' : 'offline',
                'latency' => $ai['llm']['own_model'] ? 'Modelo propio' : 'Modelo base',
                'label' => $ai['llm']['available'] ? 'Disponible' : 'No disponible',
                'detail' => 'Ollama • ' . $ai['llm']['model'],
            ];
            $classifier = [
                'status' => $ai['classifier']['status'] === 'healthy' ? 'healthy' : 'warning',
                'latency' => '-',
                'label' => $ai['classifier']['status'] === 'healthy' ? 'Entrenado' : 'Sin entrenar',
            ];
        } catch (AiServiceException $e) {
            $down = ['status' => 'offline', 'latency' => '-', 'label' => 'Sin conexión'];
            $aiNode = $vectordb = $llm = $classifier = $down;
        }

        return [
            'frontend' => ['status' => 'healthy', 'latency' => 'Navegador', 'label' => 'Online'],
            'api' => ['status' => 'healthy', 'latency' => self::ms($requestStart), 'label' => 'Online'],
            'database' => $database,
            'ai' => $aiNode,
            'vectordb' => $vectordb,
            'llm' => $llm,
            'classifier' => $classifier,
        ];
    }

    public function getNodeLogs(string $node): array
    {
        if ($node === 'api' || $node === 'database') {
            $logs = [];
            foreach ((new LogRepository())->getLogs(20, 0) as $row) {
                $type = $row['refused'] === 'unavailable' ? 'ERROR' : ($row['refused'] ? 'WARN' : 'SUCCESS');
                $status = $row['refused'] ? "rechazada ({$row['refused']})" : 'respondida';
                $latency = $row['latency_ms'] !== null ? " en {$row['latency_ms']} ms" : '';
                $logs[] = [
                    'time' => date('H:i:s', strtotime($row['created_at'])),
                    'type' => $type,
                    'source' => 'API',
                    'message' => "POST /chat • consulta #{$row['id']} {$status}{$latency}",
                ];
            }
            return array_reverse($logs);
        }

        $sources = ['vectordb' => 'vectordb', 'llm' => 'llm', 'classifier' => 'classifier', 'ai' => null];
        if (!array_key_exists($node, $sources)) {
            return [];
        }
        try {
            return $this->aiClient->logs($sources[$node])['logs'];
        } catch (AiServiceException $e) {
            return [['time' => date('H:i:s'), 'type' => 'ERROR', 'source' => 'AI', 'message' => 'Motor de IA sin conexión']];
        }
    }
}

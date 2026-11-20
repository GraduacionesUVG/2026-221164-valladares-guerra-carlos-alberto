<?php

namespace App\Controllers;

use App\Services\SystemService;
use App\Attributes\Route;
use App\Attributes\Authorize;
use Exception;

class SystemController
{
    private $systemService;

    public function __construct()
    {
        $this->systemService = new SystemService();
    }

    #[Route('/system/health', 'GET')]
    #[Authorize(['Admin'])]
    public function health()
    {
        try {
            $health = $this->systemService->getSystemHealth();
            http_response_code(200);
            echo json_encode($health);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(["error" => $e->getMessage()]);
        }
    }

    #[Route('/system/logs', 'GET')]
    #[Authorize(['Admin'])]
    public function logs()
    {
        try {
            $node = isset($_GET['node']) ? $_GET['node'] : 'api';
            $logs = $this->systemService->getNodeLogs($node);
            http_response_code(200);
            echo json_encode(["node" => $node, "logs" => $logs]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(["error" => $e->getMessage()]);
        }
    }
}

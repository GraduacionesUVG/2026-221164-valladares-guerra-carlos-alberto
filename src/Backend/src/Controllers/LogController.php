<?php

namespace App\Controllers;

use App\Services\LogService;
use App\Attributes\Route;
use App\Attributes\Authorize;
use Exception;

class LogController
{
    private $logService;

    public function __construct()
    {
        $this->logService = new LogService();
    }

    #[Route('/logs', 'GET')]
    #[Authorize(['Admin'])]
    public function index()
    {
        try {
            $page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
            $limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 10;
            
            if ($page < 1) $page = 1;
            if ($limit < 1 || $limit > 50) $limit = 10;

            $result = $this->logService->getPaginatedLogs($page, $limit);
            
            http_response_code(200);
            echo json_encode($result);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(["error" => $e->getMessage()]);
        }
    }
}

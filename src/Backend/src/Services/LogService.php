<?php

namespace App\Services;

use App\Repositories\LogRepository;

class LogService
{
    private $logRepository;

    public function __construct()
    {
        $this->logRepository = new LogRepository();
    }

    public function getPaginatedLogs(int $page = 1, int $limit = 10): array
    {
        $offset = ($page - 1) * $limit;
        
        $totalItems = $this->logRepository->getTotalLogsCount();
        $logs = $this->logRepository->getLogs($limit, $offset);
        
        $totalPages = ceil($totalItems / $limit);
        
        return [
            'data' => $logs,
            'meta' => [
                'current_page' => $page,
                'total_pages' => $totalPages,
                'total_items' => $totalItems,
                'limit' => $limit
            ]
        ];
    }
}

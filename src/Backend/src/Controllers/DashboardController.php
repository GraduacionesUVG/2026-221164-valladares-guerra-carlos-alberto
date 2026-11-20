<?php

namespace App\Controllers;

use App\Utils\Response;
use App\Attributes\Route;
use App\Attributes\Authorize;
use App\Services\DashboardService;

class DashboardController
{
    private $dashboardService;

    public function __construct()
    {
        $this->dashboardService = new DashboardService();
    }

    #[Route('/dashboard/stats', 'GET')]
    #[Authorize(['Admin'])]
    public function getStats()
    {
        $stats = $this->dashboardService->getSystemStats();
        return Response::json($stats, 200);
    }
}

<?php
// imports
use App\Core\Router;
use App\Controllers\AuthController;
use App\Controllers\ChatController;
use App\Controllers\DashboardController;
use App\Controllers\UserController;
use App\Controllers\LogController;
use App\Controllers\SystemController;
use App\Controllers\DocumentController;
use App\Controllers\RagController;
use App\Core\Config;

// Backend/api/v1/index.php

// 1. Load Autoloader
// Disable HTML error output to keep JSON valid
ini_set('display_errors', 0);
ini_set('display_startup_errors', 0);
error_reporting(E_ALL);

require_once __DIR__ . '/../../autoload.php';

// Cualquier error no controlado responde JSON genérico; el detalle va al log
set_exception_handler(function (Throwable $e) {
    error_log('[Uncaught] ' . $e->getMessage() . ' @ ' . $e->getFile() . ':' . $e->getLine());
    App\Utils\Response::error('Internal server error', 500);
});

// 2. Set Headers / CORS (solo para los orígenes configurados)
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && in_array($origin, Config::get('cors_origins', []), true)) {
    header("Access-Control-Allow-Origin: $origin");
    header("Vary: Origin");
    header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");
    header("Access-Control-Max-Age: 3600");
    header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");
}
header("Content-Type: application/json; charset=UTF-8");

// 3. Handle Preflight Options Request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// 4. Initialize Router
$router = new Router();

// 5. Register Controllers manually 
$router->registerController(AuthController::class);
$router->registerController(ChatController::class);
$router->registerController(DashboardController::class);
$router->registerController(UserController::class);
$router->registerController(LogController::class);
$router->registerController(SystemController::class);
$router->registerController(DocumentController::class);
$router->registerController(RagController::class);


// 6. Dispatch
$router->dispatch($_SERVER['REQUEST_METHOD'], $_SERVER['REQUEST_URI']);

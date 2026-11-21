<?php

namespace App\Controllers;

use App\Services\UserService;
use App\Attributes\Route;
use App\Attributes\Authorize;
use Exception;

class UserController
{
    private $userService;

    public function __construct()
    {
        $this->userService = new UserService();
    }

    #[Route('/users', 'GET')]
    #[Authorize(['Admin'])]
    public function index()
    {
        try {
            $users = $this->userService->getAllUsers();
            http_response_code(200);
            echo json_encode($users);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(["error" => $e->getMessage()]);
        }
    }

    #[Route('/users', 'POST')]
    #[Authorize(['Admin'])]
    public function store()
    {
        try {
            $data = json_decode(file_get_contents("php://input"), true);
            $user = $this->userService->createUser($data);
            
            http_response_code(201);
            echo json_encode(["message" => "User created successfully", "user" => $user]);
        } catch (Exception $e) {
            http_response_code(400);
            echo json_encode(["error" => $e->getMessage()]);
        }
    }
}

<?php

namespace App\Controllers;

use App\Services\AuthService;
use App\DTOs\Auth\LoginRequest;
use App\DTOs\Auth\LoginResponse;
use App\Utils\Response;
use App\Attributes\Route;
use Exception;

class AuthController
{
    private $authService;

    public function __construct()
    {
        $this->authService = new AuthService();
    }

    #[Route('/auth/login', 'POST')]
    public function login()
    {
        $data = json_decode(file_get_contents("php://input"), true);
        $request = new LoginRequest($data);

        if (!$request->validate()) {
            Response::error('Email and password are required', 400);
        }

        try {
            $result = $this->authService->login($request->email, $request->password);
            Response::json(new LoginResponse($result['token'], $result['user']), 200);
        } catch (Exception $e) {
            Response::error($e->getMessage(), 401);
        }
    }

    #[Route('/auth/register', 'POST')]
    public function register()
    {
        $data = json_decode(file_get_contents("php://input"), true) ?? [];

        try {
            $result = $this->authService->register(
                (string) ($data['name'] ?? ''),
                (string) ($data['email'] ?? ''),
                (string) ($data['password'] ?? '')
            );
            Response::json(new LoginResponse($result['token'], $result['user']), 201);
        } catch (Exception $e) {
            Response::error($e->getMessage(), 400);
        }
    }
}

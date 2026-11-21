<?php

namespace App\Services;

use App\Repositories\UserRepository;
use Exception;

class UserService
{
    private $userRepository;

    public function __construct()
    {
        $this->userRepository = new UserRepository();
    }

    public function getAllUsers()
    {
        return $this->userRepository->getAllUsers();
    }

    public function createUser($data)
    {
        if (empty($data['name']) || empty($data['email']) || empty($data['password']) || empty($data['role_id'])) {
            throw new Exception("Missing required fields");
        }

        if (!filter_var($data['email'], FILTER_VALIDATE_EMAIL)) {
            throw new Exception("Invalid email format");
        }

        $existingUser = $this->userRepository->findByEmail($data['email']);
        if ($existingUser) {
            throw new Exception("Email already exists");
        }

        if (strlen($data['password']) < 8) {
            throw new Exception("Password must be at least 8 characters");
        }

        $roleId = (int) $data['role_id'];
        if (!in_array($roleId, [AuthService::ROLE_ADMIN, AuthService::ROLE_USER], true)) {
            throw new Exception("Invalid role");
        }

        $passwordHash = password_hash($data['password'], PASSWORD_DEFAULT);

        $userId = $this->userRepository->createUser(
            $data['name'],
            $data['email'],
            $passwordHash,
            $roleId
        );

        if (!$userId) {
            throw new Exception("Failed to create user");
        }

        return [
            'id' => $userId,
            'name' => $data['name'],
            'email' => $data['email'],
            'role_id' => $roleId
        ];
    }
}

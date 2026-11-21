<?php

namespace App\Services;

use App\Repositories\UserRepository;
use App\Utils\JwtUtils;
use Exception;

class AuthService
{
    public const ROLE_ADMIN = 1;
    public const ROLE_USER = 2;

    private $userRepository;

    public function __construct()
    {
        $this->userRepository = new UserRepository();
    }

    public function login($email, $password)
    {
        $user = $this->userRepository->findByEmail($email);

        // Mismo mensaje para usuario inexistente o contraseña incorrecta
        if (!$user || !password_verify($password, $user->password)) {
            throw new Exception("Invalid credentials");
        }

        return ['token' => $this->issueToken($user), 'user' => $user];
    }

    /** Registro público de ciudadanos: siempre con rol User. */
    public function register(string $name, string $email, string $password)
    {
        $name = trim($name);
        $email = strtolower(trim($email));

        if ($name === '' || mb_strlen($name) > 100) {
            throw new Exception("Name is required");
        }
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throw new Exception("Invalid email format");
        }
        if (strlen($password) < 8) {
            throw new Exception("Password must be at least 8 characters");
        }
        if ($this->userRepository->findByEmail($email)) {
            throw new Exception("Email already exists");
        }

        $id = $this->userRepository->createUser($name, $email, password_hash($password, PASSWORD_DEFAULT), self::ROLE_USER);
        if (!$id) {
            throw new Exception("Failed to create user");
        }
        $user = $this->userRepository->findByEmail($email);
        return ['token' => $this->issueToken($user), 'user' => $user];
    }

    private function issueToken($user): string
    {
        return JwtUtils::generate([
            'id' => (int) $user->id,
            'email' => $user->email,
            'role_id' => (int) $user->role_id,
            'role' => (int) $user->role_id === self::ROLE_ADMIN ? 'Admin' : 'User',
        ]);
    }
}

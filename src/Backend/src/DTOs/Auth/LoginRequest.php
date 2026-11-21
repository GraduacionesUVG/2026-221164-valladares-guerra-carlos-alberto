<?php

namespace App\DTOs\Auth;

class LoginRequest
{
    public $email;
    public $password;

    public function __construct($data)
    {
        $this->email = $data['email'] ?? null;
        $this->password = $data['password'] ?? null;
    }

    public function validate()
    {
        if (empty($this->email) || empty($this->password)) {
            return false;
        }
        return true;
    }
}

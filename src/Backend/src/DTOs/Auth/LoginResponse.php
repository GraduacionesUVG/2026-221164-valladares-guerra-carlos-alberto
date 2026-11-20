<?php

namespace App\DTOs\Auth;

class LoginResponse
{
    public $token;
    public $user;

    public function __construct($token, $user)
    {
        $this->token = $token;
        $this->user = [
            'id' => $user->id,
            'name' => $user->name,
            'email' => $user->email,
            'role_id' => $user->role_id
        ];
    }
}

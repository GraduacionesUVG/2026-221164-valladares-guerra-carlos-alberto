<?php

namespace App\Entities;

class User
{
    public $id;
    public $name;
    public $email;
    public $password;
    public $role_id;
    public $created_at;

    public function __construct($id = null, $name = null, $email = null, $password = null, $role_id = null, $created_at = null)
    {
        $this->id = $id;
        $this->name = $name;
        $this->email = $email;
        $this->password = $password;
        $this->role_id = $role_id;
        $this->created_at = $created_at;
    }
}

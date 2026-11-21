<?php

namespace App\Repositories;

use App\Utils\Database;
use App\Entities\User;
use PDO;

class UserRepository
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    public function findByEmail($email)
    {
        $stmt = $this->db->prepare("SELECT * FROM users WHERE email = :email LIMIT 1");
        $stmt->bindParam(':email', $email);
        $stmt->execute();
        
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        if ($row) {
            return new User(
                $row['id'],
                $row['name'],
                $row['email'],
                $row['password'],
                $row['role_id'],
                $row['created_at']
            );
        }
        return null;
    }

    public function getAllUsers()
    {
        $stmt = $this->db->prepare("
            SELECT u.id, u.name, u.email, u.role_id, u.created_at, COALESCE(r.name, 'Admin') as role_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            ORDER BY u.created_at DESC
        ");
        $stmt->execute();
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    public function createUser($name, $email, $passwordHash, $roleId)
    {
        $stmt = $this->db->prepare("
            INSERT INTO users (name, email, password, role_id)
            VALUES (:name, :email, :password, :role_id)
        ");
        $stmt->bindParam(':name', $name);
        $stmt->bindParam(':email', $email);
        $stmt->bindParam(':password', $passwordHash);
        $stmt->bindParam(':role_id', $roleId);
        
        if ($stmt->execute()) {
            return $this->db->lastInsertId();
        }
        return false;
    }
}

<?php

namespace App\Repositories;

use App\Utils\Database;
use PDO;

class LogRepository
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    /** Consultas de los ciudadanos con su clasificación y la respuesta asociada. */
    public function getLogs(int $limit, int $offset): array
    {
        $stmt = $this->db->prepare("
            SELECT m.id, m.content AS query, m.created_at, m.topic, m.in_domain,
                   m.refused, m.latency_ms, u.name AS user_name,
                   (SELECT a.sources FROM messages a
                     WHERE a.conversation_id = m.conversation_id AND a.role = 'assistant' AND a.id > m.id
                     ORDER BY a.id ASC LIMIT 1) AS sources
            FROM messages m
            LEFT JOIN users u ON m.sender_id = u.id
            WHERE m.role = 'user'
            ORDER BY m.id DESC
            LIMIT :limit OFFSET :offset
        ");
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
        $stmt->execute();

        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        foreach ($rows as &$row) {
            $sources = $row['sources'] ? json_decode($row['sources'], true) : [];
            $row['sources'] = array_column($sources, 'reference');
        }
        return $rows;
    }

    public function getTotalLogsCount(): int
    {
        return (int) $this->db->query("SELECT COUNT(*) FROM messages WHERE role = 'user'")->fetchColumn();
    }
}

<?php

namespace App\Repositories;

use App\Utils\Database;
use PDO;

class DashboardRepository
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    private function scalar(string $sql)
    {
        return $this->db->query($sql)->fetchColumn();
    }

    public function getTotals(): array
    {
        return [
            'total_users' => (int) $this->scalar("SELECT COUNT(*) FROM users"),
            'total_conversations' => (int) $this->scalar("SELECT COUNT(*) FROM conversations"),
            'total_questions' => (int) $this->scalar("SELECT COUNT(*) FROM messages WHERE role = 'user'"),
            'out_of_domain' => (int) $this->scalar("SELECT COUNT(*) FROM messages WHERE role = 'user' AND refused = 'out_of_domain'"),
            'no_context' => (int) $this->scalar("SELECT COUNT(*) FROM messages WHERE role = 'user' AND refused = 'no_context'"),
            'avg_latency_ms' => (int) $this->scalar("SELECT COALESCE(AVG(latency_ms), 0) FROM messages WHERE role = 'assistant' AND refused IS NULL AND latency_ms IS NOT NULL"),
        ];
    }

    /** Distribución de las consultas dentro del dominio por tema clasificado. */
    public function getTopicCounts(): array
    {
        $stmt = $this->db->query("
            SELECT topic, COUNT(*) AS total
            FROM messages
            WHERE role = 'user' AND topic IS NOT NULL AND in_domain = 1
            GROUP BY topic
            ORDER BY total DESC
        ");
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    /** Consultas por día de los últimos N días. */
    public function getDailyQuestions(int $days = 14): array
    {
        $stmt = $this->db->prepare("
            SELECT DATE(created_at) AS day, COUNT(*) AS total
            FROM messages
            WHERE role = 'user' AND created_at >= DATE_SUB(CURDATE(), INTERVAL :days DAY)
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        ");
        $stmt->bindValue(':days', $days - 1, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    /** Artículos citados con más frecuencia en las respuestas. */
    public function getRecentSources(int $limit = 500): array
    {
        $stmt = $this->db->prepare("
            SELECT sources FROM messages
            WHERE role = 'assistant' AND refused IS NULL AND sources IS NOT NULL
            ORDER BY id DESC LIMIT :lim
        ");
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll(PDO::FETCH_COLUMN);
    }
}

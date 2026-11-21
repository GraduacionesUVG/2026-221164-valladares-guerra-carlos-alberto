<?php

namespace App\Repositories;

use App\Utils\Database;
use PDO;

class ChatRepository
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    public function getConversationsByUser(int $userId): array
    {
        $stmt = $this->db->prepare("
            SELECT c.id, c.title, c.created_at, c.updated_at,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count
            FROM conversations c
            WHERE c.user_id = :uid
            ORDER BY c.updated_at DESC
        ");
        $stmt->execute([':uid' => $userId]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    public function findConversation(int $conversationId): ?array
    {
        $stmt = $this->db->prepare("SELECT * FROM conversations WHERE id = :id");
        $stmt->execute([':id' => $conversationId]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        return $row ?: null;
    }

    public function createConversation(int $userId, ?string $title = null): int
    {
        $stmt = $this->db->prepare("INSERT INTO conversations (user_id, title) VALUES (:uid, :title)");
        $stmt->execute([':uid' => $userId, ':title' => $title]);
        return (int) $this->db->lastInsertId();
    }

    public function updateConversationTitle(int $conversationId, string $title): void
    {
        $stmt = $this->db->prepare("UPDATE conversations SET title = :title WHERE id = :id");
        $stmt->execute([':title' => $title, ':id' => $conversationId]);
    }

    public function touchConversation(int $conversationId): void
    {
        $stmt = $this->db->prepare("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = :id");
        $stmt->execute([':id' => $conversationId]);
    }

    public function deleteConversation(int $conversationId): void
    {
        $stmt = $this->db->prepare("DELETE FROM conversations WHERE id = :id");
        $stmt->execute([':id' => $conversationId]);
    }

    public function getMessages(int $conversationId): array
    {
        $stmt = $this->db->prepare("
            SELECT id, role, content, topic, sources, created_at
            FROM messages
            WHERE conversation_id = :cid
            ORDER BY id ASC
        ");
        $stmt->execute([':cid' => $conversationId]);
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        foreach ($rows as &$row) {
            $row['sources'] = $row['sources'] ? json_decode($row['sources'], true) : [];
        }
        return $rows;
    }

    /** Últimos turnos, en orden cronológico, para dar contexto al asistente. */
    public function getRecentTurns(int $conversationId, int $limit): array
    {
        $stmt = $this->db->prepare("
            SELECT role, content FROM messages
            WHERE conversation_id = :cid AND refused IS NULL
            ORDER BY id DESC LIMIT :lim
        ");
        $stmt->bindValue(':cid', $conversationId, PDO::PARAM_INT);
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
        $stmt->execute();
        return array_reverse($stmt->fetchAll(PDO::FETCH_ASSOC));
    }

    public function saveUserMessage(int $conversationId, int $userId, string $content): int
    {
        $stmt = $this->db->prepare("
            INSERT INTO messages (conversation_id, role, sender_id, content)
            VALUES (:cid, 'user', :sid, :content)
        ");
        $stmt->execute([':cid' => $conversationId, ':sid' => $userId, ':content' => $content]);
        return (int) $this->db->lastInsertId();
    }

    /** Guarda la respuesta del asistente y clasifica la consulta que la originó. */
    public function saveAssistantMessage(int $conversationId, int $questionId, array $reply): int
    {
        $stmt = $this->db->prepare("
            INSERT INTO messages (conversation_id, role, sender_id, content, sources, model, latency_ms, refused)
            VALUES (:cid, 'assistant', NULL, :content, :sources, :model, :latency, :refused)
        ");
        $stmt->execute([
            ':cid' => $conversationId,
            ':content' => $reply['answer'],
            ':sources' => json_encode($reply['sources'], JSON_UNESCAPED_UNICODE),
            ':model' => $reply['model'],
            ':latency' => $reply['latency_ms'],
            ':refused' => $reply['refused'],
        ]);
        $id = (int) $this->db->lastInsertId();

        // El tema y el dominio se registran en la consulta del ciudadano: son
        // la base del análisis de patrones de búsqueda (objetivo específico 3)
        $stmt = $this->db->prepare("
            UPDATE messages SET topic = :topic, in_domain = :in_domain, latency_ms = :latency, refused = :refused
            WHERE id = :id
        ");
        $stmt->execute([
            ':topic' => $reply['topic'],
            ':in_domain' => $reply['in_domain'] === null ? null : (int) $reply['in_domain'],
            ':latency' => $reply['latency_ms'],
            ':refused' => $reply['refused'],
            ':id' => $questionId,
        ]);
        return $id;
    }
}

<?php

namespace App\Services;

use App\Repositories\ChatRepository;
use DomainException;

class ChatService
{
    private const HISTORY_TURNS = 4;
    private const TITLE_LENGTH = 60;

    private $chatRepository;
    private $ragService;

    public function __construct()
    {
        $this->chatRepository = new ChatRepository();
        $this->ragService = new RagService();
    }

    public function listConversations(int $userId): array
    {
        return $this->chatRepository->getConversationsByUser($userId);
    }

    public function createConversation(int $userId): array
    {
        $id = $this->chatRepository->createConversation($userId);
        return $this->chatRepository->findConversation($id);
    }

    public function getMessages(int $userId, int $conversationId): array
    {
        $this->assertOwner($userId, $conversationId);
        return $this->chatRepository->getMessages($conversationId);
    }

    public function deleteConversation(int $userId, int $conversationId): void
    {
        $this->assertOwner($userId, $conversationId);
        $this->chatRepository->deleteConversation($conversationId);
    }

    public function handleUserMessage(int $userId, int $conversationId, string $content): array
    {
        $conversation = $this->assertOwner($userId, $conversationId);

        $history = $this->chatRepository->getRecentTurns($conversationId, self::HISTORY_TURNS);
        $questionId = $this->chatRepository->saveUserMessage($conversationId, $userId, $content);

        $reply = $this->ragService->answerQuery($content, $history);

        $replyId = $this->chatRepository->saveAssistantMessage($conversationId, $questionId, $reply);
        if (empty($conversation['title'])) {
            $this->chatRepository->updateConversationTitle($conversationId, $this->makeTitle($content));
        }
        $this->chatRepository->touchConversation($conversationId);

        return [
            'user_message_id' => $questionId,
            'reply' => [
                'id' => $replyId,
                'role' => 'assistant',
                'content' => $reply['answer'],
                'sources' => $reply['sources'],
                'topic' => $reply['topic'],
                'available' => $reply['available'],
            ],
        ];
    }

    private function assertOwner(int $userId, int $conversationId): array
    {
        $conversation = $this->chatRepository->findConversation($conversationId);
        // Se responde igual si no existe o si es de otro usuario, para no
        // revelar la existencia de conversaciones ajenas
        if (!$conversation || (int) $conversation['user_id'] !== $userId) {
            throw new DomainException('Conversation not found');
        }
        return $conversation;
    }

    private function makeTitle(string $content): string
    {
        $title = trim(preg_replace('/\s+/', ' ', $content));
        return mb_strlen($title) > self::TITLE_LENGTH
            ? mb_substr($title, 0, self::TITLE_LENGTH - 1) . '…'
            : $title;
    }
}

<?php

namespace App\Controllers;

use App\Core\Auth;
use App\Utils\Response;
use App\Attributes\Route;
use App\Attributes\Authorize;
use App\Services\ChatService;
use App\DTOs\Chat\SendMessageRequest;
use DomainException;
use Throwable;

class ChatController
{
    private $chatService;

    public function __construct()
    {
        $this->chatService = new ChatService();
    }

    #[Route('/chat/conversations', 'GET')]
    #[Authorize(['Admin', 'User'])]
    public function listConversations()
    {
        Response::json($this->chatService->listConversations(Auth::id()));
    }

    #[Route('/chat/conversations', 'POST')]
    #[Authorize(['Admin', 'User'])]
    public function createConversation()
    {
        Response::json($this->chatService->createConversation(Auth::id()), 201);
    }

    #[Route('/chat/conversations/{id}', 'DELETE')]
    #[Authorize(['Admin', 'User'])]
    public function deleteConversation($id)
    {
        try {
            $this->chatService->deleteConversation(Auth::id(), (int) $id);
            Response::json(['success' => true]);
        } catch (DomainException $e) {
            Response::error($e->getMessage(), 404);
        }
    }

    #[Route('/chat/conversations/{id}/messages', 'GET')]
    #[Authorize(['Admin', 'User'])]
    public function getMessages($id)
    {
        try {
            Response::json($this->chatService->getMessages(Auth::id(), (int) $id));
        } catch (DomainException $e) {
            Response::error($e->getMessage(), 404);
        }
    }

    #[Route('/chat/conversations/{id}/messages', 'POST')]
    #[Authorize(['Admin', 'User'])]
    public function sendMessage($id)
    {
        $request = new SendMessageRequest(json_decode(file_get_contents('php://input'), true));
        if (!$request->validate()) {
            Response::error('content is required (max ' . SendMessageRequest::MAX_LENGTH . ' characters)', 400);
        }

        try {
            $result = $this->chatService->handleUserMessage(Auth::id(), (int) $id, $request->content);
            Response::json($result, 201);
        } catch (DomainException $e) {
            Response::error($e->getMessage(), 404);
        } catch (Throwable $e) {
            error_log('[ChatController] ' . $e->getMessage());
            Response::error('Failed to send message', 500);
        }
    }
}

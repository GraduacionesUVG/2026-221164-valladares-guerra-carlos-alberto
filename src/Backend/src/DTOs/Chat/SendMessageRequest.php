<?php

namespace App\DTOs\Chat;

class SendMessageRequest
{
    public const MAX_LENGTH = 1000;

    public $content;

    public function __construct(?array $data)
    {
        $this->content = trim((string) ($data['content'] ?? ''));
    }

    public function validate(): bool
    {
        return $this->content !== '' && mb_strlen($this->content) <= self::MAX_LENGTH;
    }
}

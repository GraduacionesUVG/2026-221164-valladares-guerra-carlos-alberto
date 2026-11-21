<?php

namespace App\Controllers;

use App\Attributes\Route;
use App\Attributes\Authorize;
use App\Services\Ai\AiServiceClient;
use App\Services\Ai\AiServiceException;
use App\Utils\Response;

class DocumentController
{
    /** Documentos indexados en la base vectorial, reportados por el motor de IA. */
    #[Route('/documents', 'GET')]
    #[Authorize(['Admin'])]
    public function index()
    {
        try {
            Response::json((new AiServiceClient())->corpus());
        } catch (AiServiceException $e) {
            Response::error('Motor de IA no disponible', 503);
        }
    }
}

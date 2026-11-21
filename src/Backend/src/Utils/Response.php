<?php
namespace App\Utils;

class Response
{
    public static function json($data, $statusCode = 200)
    {
        http_response_code($statusCode);
        header('Content-Type: application/json');
        echo json_encode($data);
        exit;
    }

    public static function success($data = [], $message = 'Success', $statusCode = 200)
    {
        self::json([
            'status' => 'success',
            'message' => $message,
            'data' => $data
        ], $statusCode);
    }

    public static function error($message = 'Error', $statusCode = 400, $errors = [])
    {
        // 'error' se mantiene por compatibilidad con el frontend
        $response = [
            'status' => 'error',
            'message' => $message,
            'error' => $message
        ];

        if (!empty($errors)) {
            $response['errors'] = $errors;
        }

        self::json($response, $statusCode);
    }
}

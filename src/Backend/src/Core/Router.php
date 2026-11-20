<?php
namespace App\Core;

use App\Attributes\Route;
use App\Attributes\Authorize;
use App\Utils\Response;
use App\Utils\JwtUtils;
use ReflectionClass;
use ReflectionMethod;

class Router
{
    private $controllers = [];

    public function registerController(string $controllerClass)
    {
        $this->controllers[] = $controllerClass;
    }

    public function dispatch($method, $uri)
    {
        // Simple URI matching (ignores query params in matching logic)
        $uri = strtok($uri, '?');

        // Strip the base path if we are running in a subdirectory
        $scriptDir = str_replace('\\', '/', dirname($_SERVER['SCRIPT_NAME']));
        if ($scriptDir !== '/' && strpos($uri, $scriptDir) === 0) {
            $uri = substr($uri, strlen($scriptDir));
        }

        if ($uri === '' || $uri[0] !== '/') {
            $uri = '/' . $uri;
        }

        foreach ($this->controllers as $controllerClass) {
            $reflection = new ReflectionClass($controllerClass);

            foreach ($reflection->getMethods(ReflectionMethod::IS_PUBLIC) as $methodRef) {
                foreach ($methodRef->getAttributes(Route::class) as $attribute) {
                    $route = $attribute->newInstance();

                    // Supports parameters like /users/{id}
                    $pattern = preg_replace('/\{[a-zA-Z0-9_]+\}/', '([a-zA-Z0-9_]+)', $route->path);
                    $pattern = "@^" . $pattern . "$@D";

                    if ($route->method === $method && preg_match($pattern, $uri, $matches)) {
                        array_shift($matches);

                        $authAttrs = $methodRef->getAttributes(Authorize::class);
                        if (!empty($authAttrs)) {
                            $this->authorize($authAttrs[0]->newInstance()->roles);
                        }

                        $controllerInstance = new $controllerClass();
                        call_user_func_array([$controllerInstance, $methodRef->getName()], $matches);
                        return;
                    }
                }
            }
        }

        Response::error('Endpoint not found', 404);
    }

    private function authorize(array $requiredRoles)
    {
        $payload = $this->validateToken();
        Auth::setPayload($payload);

        if (!empty($requiredRoles) && !in_array($payload['role'] ?? 'guest', $requiredRoles, true)) {
            Response::error('Forbidden: Insufficient permissions', 403);
        }
    }

    private function validateToken(): array
    {
        $headers = function_exists('getallheaders') ? getallheaders() : [];
        $authHeader = $headers['Authorization'] ?? $headers['authorization']
            ?? $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';

        if (!preg_match('/Bearer\s(\S+)/', $authHeader, $matches)) {
            Response::error('Unauthorized: Missing Bearer Token', 401);
        }

        $payload = JwtUtils::validate($matches[1]);
        if (!$payload) {
            Response::error('Unauthorized: Invalid or expired token', 401);
        }
        return $payload;
    }
}

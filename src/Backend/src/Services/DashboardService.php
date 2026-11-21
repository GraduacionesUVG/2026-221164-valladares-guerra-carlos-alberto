<?php

namespace App\Services;

use App\Repositories\DashboardRepository;
use App\Services\Ai\AiServiceClient;
use App\Services\Ai\AiServiceException;

class DashboardService
{
    private $dashboardRepository;
    private $aiClient;

    public function __construct()
    {
        $this->dashboardRepository = new DashboardRepository();
        $this->aiClient = new AiServiceClient();
    }

    public function getSystemStats(): array
    {
        $totals = $this->dashboardRepository->getTotals();

        $topicRows = $this->dashboardRepository->getTopicCounts();
        $classified = array_sum(array_column($topicRows, 'total'));
        $topics = array_map(fn($row) => [
            'key' => $row['topic'],
            'total' => (int) $row['total'],
            'percentage' => $classified ? round($row['total'] * 100 / $classified, 1) : 0,
        ], $topicRows);

        try {
            $corpus = $this->aiClient->corpus();
            $documents = count($corpus['documents']);
            $articles = array_sum(array_column($corpus['documents'], 'articles'));
        } catch (AiServiceException $e) {
            $documents = null;
            $articles = null;
        }

        return $totals + [
            'total_documents' => $documents,
            'total_articles' => $articles,
            'classified_questions' => $classified,
            'topics' => $topics,
            'daily' => $this->dashboardRepository->getDailyQuestions(),
            'top_articles' => $this->topArticles(),
        ];
    }

    private function topArticles(int $limit = 8): array
    {
        $counts = [];
        foreach ($this->dashboardRepository->getRecentSources() as $json) {
            $sources = json_decode($json, true) ?: [];
            // Solo el fragmento más relevante de cada respuesta
            if (!empty($sources[0]['reference'])) {
                $ref = $sources[0]['reference'];
                $counts[$ref] = ($counts[$ref] ?? 0) + 1;
            }
        }
        arsort($counts);
        $out = [];
        foreach (array_slice($counts, 0, $limit, true) as $ref => $total) {
            $out[] = ['reference' => $ref, 'total' => $total];
        }
        return $out;
    }
}

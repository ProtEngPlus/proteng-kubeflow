from src.service.mq import publish_completed, publish_failed


def run_evaluation(request_body):
    try:
        results = []

        for index, mutant in enumerate(request_body.mutants):
            results.append(
                {
                    "mutation_result_id": mutant.mutation_result_id,
                    "values": {
                        "mock_score": round(0.50 + index * 0.01, 4)
                    },
                }
            )

        publish_completed(request_body, results)

    except Exception as error:
        publish_failed(request_body, error)

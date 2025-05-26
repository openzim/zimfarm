import pytest


class TestStatusGet:
    url = "/status/"

    @pytest.mark.parametrize(
        "query,expected_error_part",
        [
            pytest.param(
                "unknown_monitor?status=scraper_started&threshold_secs=5",
                "Monitor 'unknown_monitor' is not supported",
                id="unknown_monitor",
            ),
            pytest.param(
                "oldest_task_older_than?status=scraper_started",
                "threshold_secs query parameter is mandatory",
                id="threshold_secs_missing",
            ),
            pytest.param(
                "oldest_task_older_than?threshold_secs=5",
                "status query parameter is mandatory",
                id="status_missing",
            ),
        ],
    )
    def test_status_bad_queries(self, client, query, expected_error_part):
        headers = {"Content-Type": "application/json"}
        response = client.get(
            self.url + query,
            headers=headers,
        )
        assert response.status_code == 400
        response = response.json
        assert "error" in response
        assert expected_error_part in response["error"]

    @pytest.mark.parametrize(
        "query,expected_reponse",
        [
            pytest.param(
                "oldest_task_older_than?status=scraper_started&threshold_secs=500",
                "oldest_task_older_than for scraper_started and 500s: OK",
                id="oldest_task_older_than_ok",
            ),
            pytest.param(
                "oldest_task_older_than?status=scraper_started&threshold_secs=5",
                "oldest_task_older_than for scraper_started and 5s: KO",
                id="oldest_task_older_than_ko",
            ),
        ],
    )
    def test_status_normal_queries(self, client, tasks, query, expected_reponse):
        headers = {"Content-Type": "application/json"}
        response = client.get(
            self.url + "oldest_task_older_than?status=scraper_started&threshold_secs=5",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.text == "oldest_task_older_than for scraper_started and 5s: KO"

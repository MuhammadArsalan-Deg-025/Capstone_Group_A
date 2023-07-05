import os  # type: ignore
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

from requests import HTTPError

from src.matching_service.matching import get_report_category, matching_councillors


class MatchingCouncillorsTestCase(unittest.TestCase):
    @mock.patch("src.matching_service.matching.requests.get")
    @mock.patch("src.matching_service.matching.logger")
    def test_get_report_category_successful(self, mock_logger, mock_get):
        mock_response = mock.Mock()
        mock_response.json.return_value = {"category": "example_category"}
        mock_get.return_value = mock_response

        result = get_report_category(123)

        self.assertEqual(result, "example_category")
        mock_logger.info.assert_called_once_with("Report Category received.")

    @mock.patch("src.matching_service.matching.requests.get")
    @mock.patch("src.matching_service.matching.logger")
    def test_get_report_category_error(self, mock_logger, mock_get):
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = HTTPError("Test error")
        mock_response.url = f"{os.getenv('BASE_URL')}/report/123"

        mock_get.return_value = mock_response
        mock_get.return_value.status_code = 500

        with self.assertRaises(HTTPError):
            # Call the get_report_category function
            get_report_category(123)

        expected_url = f"{os.getenv('BASE_URL')}/report/123"
        mock_logger.error.assert_called_once_with(
            f"Error 500 occurred while getting {expected_url}"
        )

    @mock.patch("src.matching_service.matching.requests.get")
    def test_get_report_category_response_data(self, mock_get):
        mock_response = mock.Mock()
        mock_response.json.return_value = {"category": "example_category"}
        mock_get.return_value = mock_response

        result = get_report_category(123)

        self.assertEqual(result, "example_category")

    @patch("src.matching_service.matching.get_report_category")
    @patch("src.matching_service.matching.get_redis_client")
    @patch("json.loads")
    def test_matching_councillors_success(
        self, mock_json_loads, mock_get_redis_client, mock_get_report_category
    ):
        # Mocking the dependencies
        mock_get_report_category.return_value = "some_category"
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value.decode.return_value = '[{"councillor_id": 1, "average_value": 4.5}, {"councillor_id": 2, "average_value": 4.2}]'
        mock_get_redis_client.return_value = mock_redis_client

        # Patching the json.loads function to return the desired value
        mock_json_loads.return_value = [
            {"councillor_id": 1, "average_value": 4.5},
            {"councillor_id": 2, "average_value": 4.2},
        ]

        # Calling the function
        result = matching_councillors(12345, 2)

        # Assertions
        expected_result = [
            [
                {"councillor_id": 1, "average_value": 4.5},
                {"councillor_id": 2, "average_value": 4.2},
            ]
        ]
        self.assertEqual(result, expected_result)
        mock_get_report_category.assert_called_once_with(12345)
        mock_get_redis_client.assert_called_once()
        mock_redis_client.get.assert_called_once_with("some_category")

    @patch("src.matching_service.matching.get_report_category")
    @patch("src.matching_service.matching.json.loads")
    def test_matching_councillors_error(
        self, mock_json_loads, mock_get_report_category
    ):
        # Mocking the dependencies
        report_id = 456
        number_of_councillors = 10

        mock_get_report_category.side_effect = Exception("Error getting category")
        mock_json_loads.return_value = None

        # Calling the function
        with self.assertRaises(Exception) as context:
            matching_councillors(report_id, number_of_councillors)

        # Assertions
        mock_get_report_category.assert_called_once_with(report_id)
        mock_json_loads.assert_not_called()
        self.assertEqual(str(context.exception), "Error getting category")

    @patch("src.matching_service.matching.get_report_category")
    @patch("src.matching_service.matching.get_redis_client")
    @patch("json.loads")
    def test_matching_councillors_no_data(
        self, mock_json_loads, mock_get_redis_client, mock_get_report_category
    ):
        # Mocking the dependencies
        mock_get_report_category.return_value = "some_category"
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value.decode.return_value = None
        mock_get_redis_client.return_value = mock_redis_client

        # Patching the json.loads function to return the desired value
        mock_json_loads.return_value = []

        # Mocking the logger.info method
        mock_logger = MagicMock()

        # Importing the function after mocking the dependencies and logger
        with patch("src.matching_service.matching.logger", mock_logger):
            from src.matching_service.matching import matching_councillors

            # Calling the function
            result = matching_councillors(12345, 2)

            # Assertions
            self.assertEqual(result, [])

            mock_get_report_category.assert_called_once_with(12345)
            mock_get_redis_client.assert_called_once()
            mock_redis_client.get.assert_called_once_with("some_category")


if __name__ == "__main__":
    unittest.main()

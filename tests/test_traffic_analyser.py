import sys
import os
import unittest
import json
from datetime import datetime
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.traffic_analyser import (
    parse_args,
    load_log_entries,
    filter_entries_by_time,
    calculate_request_stats,
    calculate_http_status_rate,
    print_statistics,
)


class TestWebServerTrafficAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_log_entries = [
            {
                "timestamp": "2024-06-24 04:32:27",
                "request": "GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close",
                "response": "HTTP/1.1 200 OK\r\nContent-Length: 123\r\nConnection: close"
            },
            {
                "timestamp": "2024-06-24 04:59:33",
                "request": "PUT / HTTP/1.1\r\nHost: 127.0.0.1:8080",
                "response": "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close"
            },
            {
                "timestamp": "2024-06-24 05:08:33",
                "request": "POST /path2 HTTP/1.1\r\nHost: 127.0.0.1:8080",
                "response": "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\nConnection: close"
            },
            {
                "timestamp": "2024-06-24 05:23:04",
                "request": "GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close",
                "response": "HTTP/1.1 200 OK\r\nContent-Length: 123\r\nConnection: close"
            },
            {
                "timestamp": "2024-06-24 05:23:35",
                "request": "GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close",
                "response": "HTTP/1.1 200 OK\r\nContent-Length: 123\r\nConnection: close"
            },
        ]
        self.mock_log_file = "\n".join(
            json.dumps(entry) for entry in self.mock_log_entries
        )

    @patch("sys.stdout", new_callable=StringIO)
    def test_parse_args(self, mock_stdout):
        sys.argv = [
            "script_name.py",
            "--from",
            "2024-06-24 05:00:00",
            "--to",
            "2024-06-24 06:00:00",
        ]
        args = parse_args()
        self.assertEqual(args.start_time, "2024-06-24 05:00:00")
        self.assertEqual(args.end_time, "2024-06-24 06:00:00")

    def test_load_log_entries(self):
        log_file_path = "logs/server.log"
        with patch("builtins.open", return_value=StringIO(self.mock_log_file)):
            entries = load_log_entries(log_file_path)
        self.assertEqual(len(entries), len(self.mock_log_entries))

    def test_filter_entries_by_time(self):
        start_time = datetime.strptime("2024-06-24 05:00:00", "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime("2024-06-24 06:00:00", "%Y-%m-%d %H:%M:%S")
        filtered_entries = filter_entries_by_time(
            self.mock_log_entries, start_time, end_time
        )
        self.assertEqual(len(filtered_entries), 3)

    def test_calculate_request_stats(self):
        max_rpm, avg_rpm, percentile_95th = calculate_request_stats(
            self.mock_log_entries
        )
        self.assertAlmostEqual(max_rpm, 116.1290322580645, delta=0.1)
        self.assertAlmostEqual(avg_rpm, 0.09778357235984354, delta=0.1)
        self.assertAlmostEqual(percentile_95th, 25.2125, delta=0.1)

    def test_calculate_http_status_rate(self):
        start_time = datetime.strptime("2024-06-24 04:30:00", "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime("2024-06-24 05:30:00", "%Y-%m-%d %H:%M:%S")
        filtered_entries = filter_entries_by_time(
            self.mock_log_entries, start_time, end_time
        )

        http_status_rate = calculate_http_status_rate(filtered_entries)
        print(f"Calculated HTTP 200 OK Rate per minute: {http_status_rate}")
        self.assertAlmostEqual(http_status_rate, 0.05867014341590613, delta=0.1)  # Adjust expected value based on calculations

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_statistics(self, mock_stdout):
        start_time = "2024-06-24 05:00:00"
        end_time = "2024-06-24 06:00:00"
        max_rpm = 10.0
        avg_rpm = 2.0
        percentile_95th = 10.0

        print_statistics(start_time, end_time, max_rpm, avg_rpm, percentile_95th)
        printed_output = mock_stdout.getvalue().strip().split("\n")
        self.assertEqual(
            printed_output[0], f"Statistics from {start_time} to {end_time}"
        )
        self.assertIn(f"Maximum RPM: {max_rpm:.2f}", printed_output)
        self.assertIn(f"Average RPM: {avg_rpm:.2f}", printed_output)
        self.assertIn(f"95 percentile: {percentile_95th:.2f}", printed_output)


if __name__ == "__main__":
    unittest.main()

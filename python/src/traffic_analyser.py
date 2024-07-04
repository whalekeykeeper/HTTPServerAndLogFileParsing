import json
import argparse
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from sklearn.ensemble import IsolationForest


class LogEntry:
    def __init__(self, **kwargs: Any):
        self.timestamp = datetime.strptime(kwargs.get("timestamp"), "%Y-%m-%d %H:%M:%S")
        self.client_ip = kwargs.get("client_ip")
        self.HTTP_code = kwargs.get("HTTP_code")


class LogAnalyzer:
    def __init__(
        self,
        log_file_path: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ):
        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"File not found at {log_file_path}")

        self.log_file_path = log_file_path
        self.start_time = start_time or datetime.now() - timedelta(hours=10)
        self.end_time = end_time or datetime.now()
        self.entries = []
        self.filtered_entries = []
        self.max_rpm = 0.0
        self.avg_rpm = 0.0
        self.percentile_95th = 0.0
        self.http_status_rate = 0.0
        self.anomalies = []

    def validate_log_file(self) -> None:
        try:
            with open(self.log_file_path) as log_file:
                for line in log_file:
                    if line.strip():
                        json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in log file: {str(e)}")

    def load_log_entries(self):
        try:
            with open(self.log_file_path) as log_file:
                entries = [
                    LogEntry(**json.loads(line)) for line in log_file if line.strip()
                ]
                self.entries = entries
                return entries
        except Exception as e:
            raise RuntimeError(f"Error loading log entries: {str(e)}")

    def filter_entries_by_time(self):
        try:
            filtered_entries = [
                entry
                for entry in self.entries
                if self.start_time <= entry.timestamp <= self.end_time
            ]
            self.filtered_entries = filtered_entries
        except Exception as e:
            raise RuntimeError(f"Error filtering log entries: {str(e)}")

    def calculate_request_stats(self, entries: List[LogEntry]):
        if not entries:
            raise ValueError("No log entries provided. Cannot calculate request stats.")

        timestamps = [entry.timestamp for entry in entries]

        if len(timestamps) <= 1:
            raise ValueError(
                "Not enough timestamps to calculate request stats. At least two timestamps are required."
            )

        intervals = [
            (timestamps[i + 1] - timestamps[i]).total_seconds() / 60.0
            for i in range(len(timestamps) - 1)
        ]
        # To remove intervals which have a value of 0.0.
        # This can be handled better in the future to have more accurate logging times.
        intervals = [x for x in intervals if x != 0.0]
        if not intervals:
            raise ValueError("All intervals are zero. Cannot calculate request stats.")

        shortest_interval = min(intervals)

        max_rpm = 60 / shortest_interval
        avg_rpm = len(entries) / (
            (timestamps[-1] - timestamps[0]).total_seconds() / 60.0
        )
        percentile_95th = np.percentile(intervals, 95)
        self.max_rpm = max_rpm
        self.avg_rpm = avg_rpm
        self.percentile_95th = percentile_95th

    def calculate_http_status_rate(self, entries: List[LogEntry]):
        count_200 = sum(1 for entry in entries if "200" in entry.HTTP_code)
        timestamps = [entry.timestamp for entry in entries if "200" in entry.HTTP_code]

        if not timestamps:
            raise ValueError(
                "No timestamps found for HTTP status 200 entries. Cannot calculate HTTP status rate."
            )

        if len(timestamps) == 1:
            self.http_status_rate = count_200
            return

        total_minutes = (max(timestamps) - min(timestamps)).total_seconds() / 60.0
        if total_minutes == 0:
            raise ValueError(
                "Total duration in minutes is zero. Cannot calculate HTTP status rate."
            )

        self.http_status_rate = count_200 / total_minutes

    def detect_anomalies(self, entries: List[LogEntry]):
        if not entries:
            raise ValueError("No log entries provided. Cannot detect anomalies.")

        timestamps = [entry.timestamp for entry in entries]
        if len(timestamps) <= 1:
            raise ValueError(
                "Not enough timestamps to detect anomalies. At least two timestamps are required."
            )

        intervals = [
            (timestamps[i + 1] - timestamps[i]).total_seconds()
            for i in range(len(timestamps) - 1)
        ]

        if not intervals:
            raise ValueError("No valid intervals found. Cannot detect anomalies.")

        intervals = np.array(intervals).reshape(-1, 1)

        isolation_forest = IsolationForest(contamination=0.1)
        isolation_forest.fit(intervals)
        anomalies = isolation_forest.predict(intervals)

        self.anomalies = [
            timestamps[i + 1] for i, anomaly in enumerate(anomalies) if anomaly == -1
        ]

    def print_statistics(self) -> None:
        print(f"Statistics from {self.start_time} to {self.end_time}")
        print(f"Maximum RPM: {self.max_rpm:.2f}")
        print(f"Average RPM: {self.avg_rpm:.2f}")
        print(f"95 percentile: {self.percentile_95th:.2f}")

    def analyze(self) -> None:
        print(f"Analyzing traffic from {self.start_time} to {self.end_time}")
        self.validate_log_file()
        self.load_log_entries()
        if not self.entries:
            raise ValueError("No log entries provided. Cannot analyze traffic.")

        self.filter_entries_by_time()
        self.calculate_request_stats(self.filtered_entries)
        self.print_statistics()
        self.calculate_http_status_rate(self.filtered_entries)
        print("HTTP Status Code Rate per minute:", self.http_status_rate)

        self.detect_anomalies(self.filtered_entries)
        if self.anomalies:
            print("Anomalies detected at the following timestamps:")
            for timestamp in self.anomalies:
                print(timestamp)
        else:
            print("No anomalies detected.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Web Server Traffic Analyzer")
    parser.add_argument(
        "--from",
        dest="start_time",
        type=str,
        metavar="YYYY-MM-DD HH:MM:SS",
        help="Filter log entries from this timestamp (inclusive)",
    )
    parser.add_argument(
        "--to",
        dest="end_time",
        type=str,
        metavar="YYYY-MM-DD HH:MM:SS",
        help="Filter log entries up to this timestamp (exclusive)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        start_time = (
            datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
            if args.start_time
            else None
        )
        end_time = (
            datetime.strptime(args.end_time, "%Y-%m-%d %H:%M:%S")
            if args.end_time
            else None
        )

        analyzer = LogAnalyzer("logs/server.log", start_time, end_time)
        analyzer.analyze()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

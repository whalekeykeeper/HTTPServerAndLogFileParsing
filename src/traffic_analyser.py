import json
import argparse
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import IsolationForest


def parse_args():
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


def load_log_entries(log_file_path):
    with open(log_file_path, 'r') as log_file:
        log_entries = [json.loads(line) for line in log_file if line.strip()]
    return log_entries


def filter_entries_by_time(entries, start_time, end_time):
    filtered_entries = [entry for entry in entries if start_time <= datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') <= end_time]
    return filtered_entries


def calculate_request_stats(entries):
    if not entries:
        return 0, 0, 0

    timestamps = [
        datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S") for entry in entries
    ]

    if len(timestamps) <= 1:
        return 0, 0, 0

    intervals = [
        (timestamps[i + 1] - timestamps[i]).total_seconds() / 60.0
        for i in range(len(timestamps) - 1)
    ]
    shortest_interval = min(intervals)

    if shortest_interval <= 0:
        return 0, 0, 0

    max_rpm = 60 / shortest_interval
    avg_rpm = len(entries) / ((timestamps[-1] - timestamps[0]).total_seconds() / 60.0)
    percentile_95th = np.percentile(intervals, 95)

    return max_rpm, avg_rpm, percentile_95th


def calculate_http_status_rate(entries):
    count_200 = 0
    timestamps = []

    for entry in entries:
        response = entry.get('response')
        # TODO: Check if response contains different HTTP status codes
        if response and '200 OK' in response:
            count_200 += 1
            timestamp = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
            timestamps.append(timestamp)

    if not timestamps:
        return 0

    total_minutes = (max(timestamps) - min(timestamps)).total_seconds() / 60.0
    if total_minutes == 0:
        return count_200

    rate_per_minute = count_200 / total_minutes
    return rate_per_minute


def print_statistics(start_time, end_time, max_rpm, avg_rpm, percentile_95th):
    print(f"Statistics from {start_time} to {end_time}")
    print(f"Maximum RPM: {max_rpm:.2f}")
    print(f"Average RPM: {avg_rpm:.2f}")
    print(f"95 percentile: {percentile_95th:.2f}")


def detect_anomalies(entries):
    if not entries:
        return []

    timestamps = [
        datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S") for entry in entries
    ]
    if len(timestamps) <= 1:
        return []

    intervals = [
        (timestamps[i + 1] - timestamps[i]).total_seconds()
        for i in range(len(timestamps) - 1)
    ]
    intervals = np.array(intervals).reshape(-1, 1)

    isolation_forest = IsolationForest(contamination=0.1)
    isolation_forest.fit(intervals)
    anomalies = isolation_forest.predict(intervals)

    anomaly_timestamps = [
        timestamps[i + 1] for i, anomaly in enumerate(anomalies) if anomaly == -1
    ]

    return anomaly_timestamps


def main():
    args = parse_args()

    try:
        if args.start_time:
            start_time = datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
        else:
            start_time = datetime.now() - timedelta(hours=1)

        if args.end_time:
            end_time = datetime.strptime(args.end_time, "%Y-%m-%d %H:%M:%S")
        else:
            end_time = datetime.now()

        log_entries = load_log_entries("../logs/server.log")
        filtered_entries = filter_entries_by_time(log_entries, start_time, end_time)

        max_rpm, avg_rpm, percentile_95th = calculate_request_stats(filtered_entries)
        print_statistics(start_time, end_time, max_rpm, avg_rpm, percentile_95th)

        status_rate_per_minute = calculate_http_status_rate(filtered_entries)
        print("HTTP Status Code Rate per minute:", status_rate_per_minute)

        anomaly_timestamps = detect_anomalies(filtered_entries)
        if anomaly_timestamps:
            print("Anomalies detected at the following timestamps:")
            for timestamp in anomaly_timestamps:
                print(timestamp)
        else:
            print("No anomalies detected.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

import requests
import random
import time

"""
This is a helper function that sends requests to a given host and port.
It sends requests to random endpoints with random methods (GET, POST, PUT).
By doing so, we can simulate a load test on the server and get a log file for further parsing.
"""


def send_requests(host, port, total_duration_minutes=3, requests_per_minute=5):
    url_base = f"http://{host}:{port}"
    endpoints = ["/", "/path1", "/path2"]
    methods = ["GET", "POST", "PUT"]

    total_requests = requests_per_minute * total_duration_minutes

    requests_sent = 0

    while requests_sent < total_requests:
        endpoint = random.choice(endpoints)
        method = random.choice(methods)

        url = url_base + endpoint

        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url)
            elif method == "PUT":
                response = requests.put(url)
            else:
                print(f"Unsupported method: {method}")
                continue

            print(
                f"Request to {url} with {method} - Status Code: {response.status_code}"
            )

        except requests.exceptions.RequestException as e:
            print(f"Request to {url} with {method} failed: {e}")

        requests_sent += 1

        time.sleep(random.uniform(0.5, 2.0))

    print("Finished sending requests.")


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8080
    send_requests(host, port)

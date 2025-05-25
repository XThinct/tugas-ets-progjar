import socket
import json
import base64
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

class FileTransferClient:
    def __init__(self, host, port):
        self.target = (host, port)
        self.timeout_duration = 300  

    def send_request(self, command):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout_duration)
        try:
            sock.connect(self.target)
            sock.sendall((command + "\r\n\r\n").encode())

            received = ""
            while True:
                chunk = sock.recv(1024 * 1024)
                if chunk:
                    received += chunk.decode()
                    if "\r\n\r\n" in received:
                        break
                else:
                    break

            parsed = received.split("\r\n\r\n")[0]
            return json.loads(parsed)
        except Exception as err:
            return {"status": "ERROR", "data": str(err)}
        finally:
            sock.close()

    def fetch_file_list(self):
        response = self.send_request("LIST")
        if response["status"] == "OK":
            return True, response["data"]
        return False, response.get("data", "Unknown failure")

    def download_file(self, filename):
        start = time.time()
        response = self.send_request(f"GET {filename}")
        if response["status"] == "OK":
            try:
                fname = response["data_namafile"]
                content = base64.b64decode(response["data_file"])
                with open(fname, "wb+") as out_file:
                    out_file.write(content)
                duration = time.time() - start
                return True, duration, os.path.getsize(fname)
            except Exception:
                return False, 0, 0
        return False, 0, 0

    def upload_file(self, filepath):
        start = time.time()
        if not os.path.isfile(filepath):
            return False, 0, 0

        try:
            with open(filepath, "rb") as in_file:
                file_size = os.path.getsize(filepath)
                encoded_data = base64.b64encode(in_file.read()).decode()

            response = self.send_request(f"UPLOAD {filepath} {encoded_data}")
            duration = time.time() - start

            if response and response.get("status") == "OK":
                return True, duration, file_size
            return False, 0, 0
        except Exception:
            return False, 0, 0

def execute_task(client, job):
    action, filename = job
    if action == "download":
        return client.download_file(filename)
    elif action == "upload":
        return client.upload_file(filename)
    elif action == "list":
        return client.fetch_file_list()[0], 0, 0
    return False, 0, 0

def run_stress_test(ip, port, action, file, worker_count):
    client = FileTransferClient(ip, port)
    job_list = [(action, file) for _ in range(worker_count)]

    start = time.time()
    outcome = []

    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = [pool.submit(execute_task, client, job) for job in job_list]
        for future in as_completed(futures):
            outcome.append(future.result())

    duration = time.time() - start
    successful = sum(1 for r in outcome if r[0])
    failed = len(outcome) - successful

    if action in ["download", "upload"] and successful > 0:
        total_bytes = sum(r[2] for r in outcome if r[0])
        rate = total_bytes / duration
    else:
        rate = 0

    return {
        "operation": action,
        "file_size": os.path.getsize(file) if file and os.path.exists(file) else 0,
        "num_workers": worker_count,
        "total_time": duration,
        "throughput": rate,
        "successes": successful,
        "failures": failed
    }

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--server-ip", default="172.16.16.101")
    arg_parser.add_argument("--server-port", type=int, default=7778)
    arg_parser.add_argument("--operation", choices=["download", "upload"], required=True)
    arg_parser.add_argument("--filename")
    arg_parser.add_argument("--workers", type=int, default=5)
    args = arg_parser.parse_args()

    if args.operation in ["download", "upload"] and not args.filename:
        print("Filename must be specified for upload/download operations.")
        exit(1)

    logging.basicConfig(level=logging.WARNING)
    stats = run_stress_test(args.server_ip, args.server_port, args.operation, args.filename, args.workers)

    print("\n--- Stress Test Report ---")
    print(f"Operation   : {stats['operation']}")
    if args.operation in ["download", "upload"]:
        print(f"File Size   : {stats['file_size'] / 1024 / 1024:.2f} MB")
    print(f"Workers     : {stats['num_workers']}")
    print(f"Total Time  : {stats['total_time']:.2f} seconds")
    if args.operation in ["download", "upload"]:
        print(f"Throughput  : {stats['throughput'] / 1024 / 1024:.2f} MB/s")
    print(f"Successes   : {stats['successes']}")
    print(f"Failures    : {stats['failures']}")

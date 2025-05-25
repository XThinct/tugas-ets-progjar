import os
import time
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from file_client_threadpool import FileTransferClient  

class StressTester:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.test_data = []
        self.test_file_map = {
            'small': 'test_10mb.dat',
            'medium': 'test_50mb.dat',
            'large': 'test_100mb.dat'
        }

    def check_files(self):
        for label, path in self.test_file_map.items():
            if not os.path.exists(path):
                print(f"[ERROR] Missing required file: {path}")
                return False
        return True

    def execute_test(self, action, file_path, client_count, server_pool_size):
        size_in_bytes = os.path.getsize(file_path)
        print(f"\n{action.upper()} | File: {file_path} | Size: {size_in_bytes / (1024**2):.2f} MB | Clients: {client_count} | Server Threads: {server_pool_size}")
        
        client_instance = FileTransferClient(self.server_ip, self.server_port)

        start = time.time()
        with ThreadPoolExecutor(max_workers=client_count) as executor:
            tasks = []
            for _ in range(client_count):
                if action == "upload":
                    tasks.append(executor.submit(client_instance.upload_file, file_path))
                else:
                    tasks.append(executor.submit(client_instance.download_file, file_path))

            results = [task.result() for task in tasks]

        duration = time.time() - start
        successful = sum(1 for res in results if res[0])
        failed = client_count - successful
        transferred_bytes = sum(res[2] for res in results if res[0])
        throughput = (transferred_bytes / duration) / (1024**2) if duration > 0 else 0
        avg_duration = sum(res[1] for res in results) / client_count if client_count > 0 else 0

        record = {
            'timestamp': datetime.now().isoformat(),
            'operation': action,
            'volume': f"{size_in_bytes // (1024*1024)} MB",
            'client_workers': client_count,
            'server_workers': server_pool_size,
            'total_time': round(duration, 2),
            'throughput': round(throughput, 2),
            'client_success': successful,
            'client_fail': failed,
            'server_success': successful,
            'server_fail': failed,
        }
        self.test_data.append(record)
        self.display_result(record)
        return record

    def display_result(self, data):
        print("\nRingkasan Pengujian:")
        print(f"Operasi:                {data['operation'].upper()}")
        print(f"Volume File:            {data['volume']}")
        print(f"Jumlah Client Worker:   {data['client_workers']}")
        print(f"Jumlah Server Worker:   {data['server_workers']}")
        print(f"Durasi Total:           {data['total_time']} detik")
        print(f"Throughput:             {data['throughput']} MB/s")
        print(f"Client Sukses:          {data['client_success']}")
        print(f"Client Gagal:           {data['client_fail']}")
        print(f"Server Sukses:          {data['server_success']}")
        print(f"Server Gagal:           {data['server_fail']}")

    def run_all_tests(self):
        if not self.check_files():
            return False

        ops = ['download', 'upload']
        sizes = ['small', 'medium', 'large']
        client_levels = [1, 5, 50]
        server_levels = [50]

        test_index = 1
        total_tests = len(ops) * len(sizes) * len(client_levels) * len(server_levels)

        for op in ops:
            for sz in sizes:
                for clients in client_levels:
                    for servers in server_levels:
                        print(f"\n[Running Test {test_index}/{total_tests}]")
                        file_to_test = self.test_file_map[sz]
                        self.execute_test(op, file_to_test, clients, servers)
                        time.sleep(5)
                        test_index += 1
        return True

    def export_to_csv(self, out_file="stress_test_results.csv"):
        if not self.test_data:
            print("[WARNING] No results to export.")
            return False

        columns = [
            'timestamp', 'operation', 'volume', 'client_workers', 'server_workers',
            'total_time', 'throughput', 'client_success', 'client_fail',
            'server_success', 'server_fail'
        ]

        try:
            with open(out_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(self.test_data)
            print(f"[INFO] Results exported to {out_file}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to write CSV: {e}")
            return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stress Test Automation for File Transfer Server")
    parser.add_argument("--server-ip", default="172.16.16.101")
    parser.add_argument("--server-port", type=int, default=7778)
    parser.add_argument("--single-test", action="store_true")
    parser.add_argument("--operation", choices=["upload", "download"])
    parser.add_argument("--file-size", choices=["small", "medium", "large"])
    parser.add_argument("--client-workers", type=int)
    parser.add_argument("--server-workers", type=int, default=1)
    parser.add_argument("--output", default="stress_test_results.csv")

    args = parser.parse_args()

    tester = StressTester(args.server_ip, args.server_port)

    if args.single_test:
        if not all([args.operation, args.file_size, args.client_workers]):
            print("[ERROR] Missing arguments for single test: --operation, --file-size, --client-workers")
            exit(1)

        test_file = tester.test_file_map[args.file_size]
        tester.execute_test(args.operation, test_file, args.client_workers, args.server_workers)
    else:
        print("[INFO] Running full test suite...")
        tester.run_all_tests()

    tester.export_to_csv(args.output)

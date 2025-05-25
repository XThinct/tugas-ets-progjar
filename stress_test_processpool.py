import os
import time
import csv
from datetime import datetime
from file_client_processpool import run_stress_test

class ProcessPoolStressAutomator:
    def __init__(self, ip_address, port_number):
        self.ip = ip_address
        self.port = port_number
        self.test_results = []
        self.file_variants = {
            'small': 'test_10mb.dat',
            'medium': 'test_50mb.dat',
            'large': 'test_100mb.dat'
        }

    def verify_files_exist(self):
        """Cek apakah file pengujian tersedia"""
        for label, path in self.file_variants.items():
            if not os.path.isfile(path):
                print(f"File {path} tidak ditemukan.")
                return False
        return True

    def execute_test_case(self, method, filepath, clients):
        """Lakukan satu pengujian stress menggunakan ProcessPoolExecutor"""
        volume = os.path.getsize(filepath)
        print(f"\n{method.upper()} | File: {filepath} | Ukuran: {volume / 1024 / 1024:.2f} MB | Worker: {clients}")

        result = run_stress_test(self.ip, self.port, method, filepath, clients)

        success_count = result.get('successes', 0)
        fail_count = result.get('failures', 0)
        summary = {
            'timestamp': datetime.now().isoformat(),
            'operation': result.get('operation'),
            'volume': f"{volume // (1024*1024)} MB",
            'client_workers': result.get('num_workers'),
            'total_time': round(result.get('total_time', 0), 2),
            'throughput': round((result.get('throughput', 0) / (1024*1024)), 2),
            'client_success': success_count,
            'client_fail': fail_count,
            'server_success': success_count,  
            'server_fail': fail_count         
        }

        self.test_results.append(summary)
        self.display_test_summary(summary)
        return summary

    def display_test_summary(self, data):
        """Tampilkan ringkasan hasil pengujian"""
        print("\nRingkasan Pengujian:")
        print(f"Operasi:         {data['operation'].upper()}")
        print(f"Volume File:     {data['volume']}")
        print(f"Jumlah Worker:   {data['client_workers']}")
        print(f"Durasi Total:    {data['total_time']} detik")
        print(f"Throughput:      {data['throughput']} MB/s")
        print(f"Client Sukses:   {data['client_success']}")
        print(f"Client Gagal:    {data['client_fail']}")
        print(f"Server Sukses:   {data['server_success']}")
        print(f"Server Gagal:    {data['server_fail']}")

    def run_all_combinations(self):
        """Eksekusi seluruh kombinasi pengujian"""
        if not self.verify_files_exist():
            return False

        methods = ['download', 'upload']
        sizes = ['small', 'medium', 'large']
        client_counts = [1, 5, 50]
        total_tests = len(methods) * len(sizes) * len(client_counts)
        index = 1

        for op in methods:
            for size in sizes:
                for count in client_counts:
                    print(f"\nMenjalankan tes {index}/{total_tests} ...")
                    test_file = self.file_variants[size]
                    self.execute_test_case(op, test_file, count)
                    time.sleep(5)
                    index += 1
        return True

    def export_results_to_csv(self, output_file="stress_results_processpool.csv"):
        """Simpan hasil pengujian ke file CSV"""
        if not self.test_results:
            print("Tidak ada data untuk disimpan.")
            return False

        columns = [
            'timestamp', 'operation', 'volume', 'client_workers',
            'total_time', 'throughput', 'client_success', 'client_fail',
            'server_success', 'server_fail'
        ]

        try:
            with open(output_file, 'w', newline='') as csv_out:
                writer = csv.DictWriter(csv_out, fieldnames=columns)
                writer.writeheader()
                writer.writerows(self.test_results)
            print(f"\nHasil pengujian disimpan di {output_file}")
            return True
        except Exception as error:
            print(f"Gagal menyimpan hasil: {error}")
            return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Otomasi Stress Test - ProcessPool")
    parser.add_argument("--server-ip", default="172.16.16.101", help="Alamat IP server")
    parser.add_argument("--server-port", type=int, default=7779, help="Port server")
    parser.add_argument("--single-test", action="store_true", help="Jalankan satu pengujian saja")
    parser.add_argument("--operation", choices=["upload", "download"], help="Jenis operasi")
    parser.add_argument("--file-size", choices=["small", "medium", "large"], help="Ukuran file")
    parser.add_argument("--workers", type=int, help="Jumlah worker client")
    parser.add_argument("--output", default="stress_results_processpool.csv", help="Nama file hasil CSV")
    args = parser.parse_args()

    executor = ProcessPoolStressAutomator(args.server_ip, args.server_port)

    if args.single_test:
        if not all([args.operation, args.file_size, args.workers]):
            print("Error: Untuk pengujian tunggal, parameter --operation, --file-size, dan --workers wajib diisi.")
            exit(1)
        selected_file = executor.file_variants[args.file_size]
        executor.execute_test_case(args.operation, selected_file, args.workers)
    else:
        print("Menjalankan semua skenario stress test (ProcessPool)...")
        executor.run_all_combinations()

    executor.export_results_to_csv(args.output)

import socket
import logging
import sys
from concurrent.futures import ProcessPoolExecutor
from file_protocol import FileProtocol

def setup_worker():
    global protocol_handler
    protocol_handler = FileProtocol()

def process_client(conn, addr):
    data_buffer = ""
    try:
        while True:
            chunk = conn.recv(1024 * 1024)
            if not chunk:
                break
            data_buffer += chunk.decode()

            while "\r\n\r\n" in data_buffer:
                raw_command, data_buffer = data_buffer.split("\r\n\r\n", 1)
                logging.warning(f"Command diterima: {raw_command[:50]}...")  
                response_data = protocol_handler.proses_string(raw_command)
                complete_response = response_data + "\r\n\r\n"
                conn.sendall(complete_response.encode())
    except Exception as err:
        logging.error(f"Gagal menangani klien {addr}: {str(err)}")
    finally:
        conn.close()
        logging.warning(f"Koneksi dari {addr} ditutup")

class FileServer:
    def __init__(self, host="0.0.0.0", port=7779, max_workers=5):
        self.server_address = (host, port)
        self.worker_limit = max_workers
        self.pool = ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=setup_worker
        )
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        logging.warning(f"Server aktif di {self.server_address} dengan {self.worker_limit} proses")
        self.sock.bind(self.server_address)
        self.sock.listen(100)

        try:
            while True:
                client_conn, client_addr = self.sock.accept()
                logging.warning(f"Klien baru: {client_addr}")
                self.pool.submit(process_client, client_conn, client_addr)
        except KeyboardInterrupt:
            logging.warning("Server dihentikan...")
        finally:
            self.pool.shutdown()
            self.sock.close()

if __name__ == "__main__":
    worker_count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    logging.basicConfig(level=logging.WARNING)
    server = FileServer(host="0.0.0.0", port=7779, max_workers=worker_count)
    server.run()

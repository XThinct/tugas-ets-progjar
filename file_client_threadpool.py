from socket import *
import socket
import threading
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from file_protocol import FileProtocol

file_handler = FileProtocol()

class FileTransferThreadServer:
    def __init__(self, host="0.0.0.0", port=7778, thread_limit=5):
        self.server_address = (host, port)
        self.thread_limit = thread_limit
        self.executor = ThreadPoolExecutor(max_workers=thread_limit)
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        logging.warning(f"[ACTIVE] Server listening on {self.server_address} with {self.thread_limit} threads")
        self.listener.bind(self.server_address)
        self.listener.listen(100)
        
        try:
            while True:
                client_sock, client_info = self.listener.accept()
                logging.warning(f"[NEW CLIENT] {client_info} connected")
                self.executor.submit(self.process_client, client_sock, client_info)
        except KeyboardInterrupt:
            logging.warning("[SHUTDOWN] Server manually stopped.")
        finally:
            self.executor.shutdown()
            self.listener.close()

    def process_client(self, sock, client_info):
        input_buffer = ""
        try:
            while True:
                packet = sock.recv(1024 * 1024)  
                if not packet:
                    break
                input_buffer += packet.decode()
                while "\r\n\r\n" in input_buffer:
                    command_block, input_buffer = input_buffer.split("\r\n\r\n", 1)
                    logging.warning(f"[COMMAND] From {client_info}: {command_block[:50]}...")
                    response_block = file_handler.proses_string(command_block)
                    sock.sendall((response_block + "\r\n\r\n").encode())
        except Exception as err:
            logging.error(f"[ERROR] While handling {client_info}: {str(err)}")
        finally:
            sock.close()
            logging.warning(f"[DISCONNECT] {client_info} connection closed.")

if __name__ == "__main__":
    threads = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    logging.basicConfig(level=logging.WARNING)
    server_instance = FileTransferThreadServer(host="0.0.0.0", port=7778, thread_limit=threads)
    server_instance.run()

import socket
import json
import base64
import logging
import os

server_address=('0.0.0.0',7777)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message ")
        sock.sendall(command_str.encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received="" #empty string
        while True:
            #socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            data = sock.recv(16)
            if data:
                #data is not empty, concat with previous content
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                # no more data, stop the process by break
                break
        # at this point, data_received (string) will contain all data coming from the socket
        # to be able to use the data_received as a dict, need to load it using json.loads()
        hasil = json.loads(data_received)
        logging.warning("data received from server:")
        return hasil
    except:
        logging.warning("error during data receiving")
        return False

def remote_list():
    command_str=f"LIST"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print("daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False

def remote_get(filename=""):
    command_str=f"GET {filename}"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        #proses file dalam bentuk base64 ke bentuk bytes
        namafile= hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        fp = open(namafile,'wb+')
        fp.write(isifile)
        fp.close()
        return True
    else:
        print("Gagal")
        return False

def upload_file_to_server(filepath=""):
    if not os.path.isfile(filepath):
        print(f"File '{filepath}' tidak ditemukan.")
        return False

    try:
        with open(filepath, 'rb') as file:
            encoded_file = base64.b64encode(file.read()).decode()

        filename_only = os.path.basename(filepath)
        command = f"UPLOAD {filename_only} {encoded_file}"

        response = send_command(command)

        if response and response.get('status') == 'OK':
            print(response['data'])
            return True
        else:
            print(f"Gagal: {response.get('data', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"Error saat upload: {str(e)}")
        return False

def delete_file_from_server(filename=""):
    command = f"DELETE {filename}"
    response = send_command(command)

    if response and response.get('status') == 'OK':
        print(response['data'])
        return True
    else:
        print(f"Gagal: {response.get('data', 'Unknown error')}")
        return False

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)

    print("=" * 60)
    print("REMOTE FILE CLIENT".center(60))
    print("=" * 60)

    while True:
        print("\nAvailable Commands:")
        print("  [1] List files on server")
        print("  [2] Download a file from server")
        print("  [3] Upload a file to server")
        print("  [4] Delete a file on server")
        print("  [5] Exit")
        print("-" * 60)

        choice = input("Enter your choice (1-5): ").strip()

        if choice == '1':
            print("\nRequesting file list from server...")
            remote_list()

        elif choice == '2':
            filename = input("Enter the filename to download: ").strip()
            print(f"Downloading '{filename}'...")
            success = remote_get(filename)
            if success:
                print("Download completed successfully.")
            else:
                print("Download failed.")

        elif choice == '3':
            filepath = input("Enter the full path of the file to upload: ").strip()
            print(f"Uploading '{filepath}' to server...")
            success = upload_file_to_server(filepath)
            if success:
                print("Upload completed successfully.")
            else:
                print("Upload failed.")

        elif choice == '4':
            filename = input("Enter the filename to delete on server: ").strip()
            print(f"Deleting '{filename}' from server...")
            success = delete_file_from_server(filename)
            if success:
                print("File deleted successfully.")
            else:
                print("File deletion failed.")

        elif choice == '5':
            print("Exiting client program.")
            break

        else:
            print("Invalid input. Please enter a number from 1 to 5.")
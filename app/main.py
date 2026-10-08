import socket
import threading
import sys
import os


def handle_client(client, directory):
    request = client.recv(1024).decode()

    request_line = request.split("\r\n")[0]
    parts = request_line.split()
    path = parts[1]

    if path.startswith("/echo/"):
        body = path[len("/echo/"):]

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(body)}\r\n"
            "\r\n"
            f"{body}"
        ).encode()

    elif path == "/user-agent":
        headers = request.split("\r\n")[1:]

        user_agent = ""

        for header in headers:
            if header.lower().startswith("user-agent:"):
                user_agent = header.split(":", 1)[1].strip()
                break

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(user_agent)}\r\n"
            "\r\n"
            f"{user_agent}"
        ).encode()

    elif path.startswith("/files/"):
        if directory is None:
            response = b"HTTP/1.1 404 Not Found\r\n\r\n"
        else:
            filename = path[len("/files/"):]
            file_path = os.path.join(directory, filename)

            if os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    body = file.read()

                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: application/octet-stream\r\n"
                    + f"Content-Length: {len(body)}\r\n".encode()
                    + b"\r\n"
                    + body
                )
            else:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"

    elif path == "/":
        response = b"HTTP/1.1 200 OK\r\n\r\n"

    else:
        response = b"HTTP/1.1 404 Not Found\r\n\r\n"

    client.sendall(response)
    client.close()


def main():
    directory = None

    if len(sys.argv) >= 3 and sys.argv[1] == "--directory":
        directory = sys.argv[2]

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind(("localhost", 4221))

    server.listen(5)

    while True:
        client, address = server.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(client, directory)
        )

        thread.start()


if __name__ == "__main__":
    main()

import socket
import threading
import sys
import os
import gzip


def handle_client(client, directory):
    request = client.recv(1024).decode()

    while "\r\n\r\n" not in request:
        request += client.recv(1024).decode()

    request_line = request.split("\r\n")[0]

    parts = request_line.split()

    method = parts[0]
    path = parts[1]

    headers = request.split("\r\n")[1:]

    accept_encoding = ""

    for header in headers:
        if header.lower().startswith("accept-encoding:"):
            accept_encoding = header.split(":", 1)[1].strip()
            break

    if path.startswith("/echo/") and method == "GET":
        body = path[len("/echo/"):].encode()

        if "gzip" in accept_encoding.split():
            body = gzip.compress(body)

            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                b"Content-Encoding: gzip\r\n"
                + f"Content-Length: {len(body)}\r\n".encode()
                + b"\r\n"
                + body
            )

        else:
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                + f"Content-Length: {len(body)}\r\n".encode()
                + b"\r\n"
                + body
            )

    elif path == "/user-agent" and method == "GET":
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

    elif path == "/" and method == "GET":
        response = b"HTTP/1.1 200 OK\r\n\r\n"

    elif path.startswith("/files/"):
        filename = path[len("/files/"):]

        if directory is None:
            response = b"HTTP/1.1 404 Not Found\r\n\r\n"

        else:
            file_path = os.path.join(directory, filename)

            if method == "GET":

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

            elif method == "POST":

                headers = request.split("\r\n")

                content_length = 0

                for header in headers:
                    if header.lower().startswith("content-length:"):
                        content_length = int(
                            header.split(":", 1)[1].strip()
                        )
                        break

                body_start = request.find("\r\n\r\n") + 4

                body = request[body_start:]

                while len(body.encode()) < content_length:
                    body += client.recv(1024).decode()

                with open(file_path, "w") as file:
                    file.write(body[:content_length])

                response = b"HTTP/1.1 201 Created\r\n\r\n"

            else:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"

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

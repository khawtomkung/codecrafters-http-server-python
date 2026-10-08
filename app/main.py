import socket
import threading
import sys
import os
import gzip


def handle_client(client, directory):
    try:
        while True:
            request = client.recv(1024).decode()

            if not request:
                break

            while "\r\n\r\n" not in request:
                data = client.recv(1024).decode()

                if not data:
                    client.close()
                    return

                request += data

            request_line = request.split("\r\n")[0]
            parts = request_line.split()

            if len(parts) < 2:
                break

            method = parts[0]
            path = parts[1]

            header_section, _, body = request.partition("\r\n\r\n")
            headers = header_section.split("\r\n")[1:]

            accept_encoding = ""

            for header in headers:
                if header.lower().startswith("accept-encoding:"):
                    accept_encoding = header.split(":", 1)[1].strip()
                    break

            content_length = 0

            for header in headers:
                if header.lower().startswith("content-length:"):
                    content_length = int(
                        header.split(":", 1)[1].strip()
                    )
                    break

            body_bytes = body.encode()

            while len(body_bytes) < content_length:
                data = client.recv(1024)

                if not data:
                    return

                body_bytes += data

            if path.startswith("/echo/") and method == "GET":
                body = path[len("/echo/"):].encode()

                encodings = [
                    encoding.strip()
                    for encoding in accept_encoding.split(",")
                ]

                if "gzip" in encodings:
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
                user_agent = ""

                for header in headers:
                    if header.lower().startswith("user-agent:"):
                        user_agent = header.split(":", 1)[1].strip()
                        break

                body = user_agent.encode()

                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    + f"Content-Length: {len(body)}\r\n".encode()
                    + b"\r\n"
                    + body
                )

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
                        with open(file_path, "wb") as file:
                            file.write(body_bytes[:content_length])

                        response = b"HTTP/1.1 201 Created\r\n\r\n"

                    else:
                        response = b"HTTP/1.1 404 Not Found\r\n\r\n"

            else:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"

            connection_close = any(
                header.lower().strip() == "connection: close"
                for header in headers
            )

            if connection_close:
                response = response.replace(
                    b"\r\n\r\n",
                    b"\r\nConnection: close\r\n\r\n",
                    1
                )

            client.sendall(response)

            if connection_close:
                break

    finally:
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

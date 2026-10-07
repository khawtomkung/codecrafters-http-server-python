import socket  # noqa: F401


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind(("localhost", 4221))

    server.listen(5)

    while True:
        client, address = server.accept()

        request = client.recv(1024).decode()

        request_line = request.split("\r\n")[0]

        parts = request_line.split()

        path = parts[1]

        if path == "/":
            response = "HTTP/1.1 200 OK\r\n\r\n"
        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\n"

        client.sendall(response.encode())

        client.close()

if __name__ == "__main__":
    main()

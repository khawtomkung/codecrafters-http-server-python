import socket  # noqa: F401

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind(("localhost", 4221))

server.listen(5)

while True:
    client, address = server.accept()

    client.recv(1024)

    response = "HTTP/1.1 200 OK\r\n\r\n"

    client.sendall(response.encode())

    client.close()


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    server_socket.accept()  # wait for client


if __name__ == "__main__":
    main()

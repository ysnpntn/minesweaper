import socket

def receive_message(conn):
    data = b""
    while True:
        chunk = conn.recv(1)
        if chunk == b"\n" or not chunk:
            break
        data += chunk
    return data.decode().strip()


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 5555))

    while True:
        server_msg = receive_message(client)
        print(server_msg)

        if "Введите X Y" in server_msg or "Ваш ход" in server_msg:
            while True:
                try:
                    coords = input("> ")
                    x, y = map(int, coords.split())
                    client.send(f"{x} {y}\n".encode())
                    break
                except ValueError:
                    print("Ошибка! Введите два числа через пробел (например: 1 2).")

        elif "победили" in server_msg or "проиграли" in server_msg:
            break

    client.close()


if __name__ == "__main__":
    main()
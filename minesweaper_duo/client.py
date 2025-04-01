import socket
import sys


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 5555))

    try:
        while True:
            data = client.recv(1024).decode().strip()
            if not data:
                break

            print(data)

            if "Введите координаты" in data or "Мина" in data:
                while True:
                    try:
                        coords = input("> ")
                        x, y = map(int, coords.split())
                        if 0 <= x <= 4 and 0 <= y <= 4:
                            client.send(f"{x} {y}\n".encode())
                            break
                        else:
                            print("Координаты должны быть от 0 до 4!")
                    except ValueError:
                        print("Ошибка: введите два числа через пробел (например, 2 2).")

            elif "победили" in data or "проиграли" in data:
                break

    finally:
        client.close()


if __name__ == "__main__":
    main()
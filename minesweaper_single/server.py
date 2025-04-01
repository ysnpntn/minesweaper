import socket
import threading

HOST = '127.0.0.1'
PORT = 5555
FIELD_SIZE = 5
MINES_COUNT = 5

class Player:
    def __init__(self, conn, addr, player_id):
        self.conn = conn
        self.addr = addr
        self.id = player_id
        self.mines = set()
        self.hits = set()
        self.opponent_hits = 0

    def send_message(self, message):
        self.conn.send((message + "\n").encode())

    def receive_message(self):
        data = b""
        while True:
            chunk = self.conn.recv(1)
            if chunk == b"\n" or not chunk:
                break
            data += chunk
        return data.decode().strip()


class Game:
    def __init__(self):
        self.players = []
        self.current_turn = 0
        self.game_over = False
        self.lock = threading.Lock()

    def add_player(self, conn, addr):
        player = Player(conn, addr, len(self.players))
        self.players.append(player)
        return player

    def setup_mines(self, player):
        player.send_message(
            f"Расставьте {MINES_COUNT} мин. Вводите по одной координате (X Y, от 0 до {FIELD_SIZE - 1}):")
        mines_received = 0
        while mines_received < MINES_COUNT:
            player.send_message(f"Вы ставите мину {mines_received + 1}/{MINES_COUNT}. Введите X Y:")
            data = player.receive_message()
            try:
                x, y = map(int, data.split())
                if not (0 <= x < FIELD_SIZE and 0 <= y < FIELD_SIZE):
                    player.send_message(f"Ошибка! Координаты должны быть от 0 до {FIELD_SIZE - 1}.")
                    continue
                if (x, y) in player.mines:
                    player.send_message("Здесь уже установлена мина! Выберите другую координату.")
                    continue
                player.mines.add((x, y))
                mines_received += 1
                player.send_message(f"Мина установлена на ({x}, {y}). Осталось установить {MINES_COUNT - mines_received} мин.")
            except ValueError:
                player.send_message("Ошибка! Введите два числа через пробел (например: 1 2).")

    def play_turn(self, player):
        opponent = self.players[1 - player.id]

        while True:

            player.send_message("Ваш ход! Введите координаты через пробел (X Y) для выстрела (0-4):")

            data = player.receive_message()
            try:
                x, y = map(int, data.split())

                if not (0 <= x < FIELD_SIZE and 0 <= y < FIELD_SIZE):
                    player.send_message(f"Ошибка! Координаты должны быть от 0 до {FIELD_SIZE - 1}.")
                    continue

                if (x, y) in player.hits:
                    player.send_message("Данные координаты были введены вами ранее! Введите другие.")
                    continue

                player.hits.add((x, y))

                if (x, y) in opponent.mines:
                    player.opponent_hits += 1
                    opponent.mines.remove((x, y))
                    player.send_message(f"Вы подорвались на мине противника на координатах ({x}, {y}).")
                    opponent.send_message(f"Противник попал на вашу мину на ({x}, {y})!")

                    if player.opponent_hits == MINES_COUNT:
                        player.send_message("Вы подорвались на всех минах противника. Вы проиграли.")
                        opponent.send_message("Оппонент подорвался на всех ваших минах. Вы победили.")
                        self.game_over = True
                        return
                else:
                    player.send_message("На данной координате мины нет.")

                self.current_turn = 1 - self.current_turn
                break

            except ValueError:
                player.send_message("Ошибка! Введите два числа через пробел (например: 1 2).")
                continue

    def run(self):
        for player in self.players:
            self.setup_mines(player)
            player.send_message("Все мины расставлены. Ожидайте начала игры...")

        while not self.game_over:
            current_player = self.players[self.current_turn]
            if self.play_turn(current_player):
                break

        for player in self.players:
            player.conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(2)
    print(f"Сервер запущен на {HOST}:{PORT}. Ожидание игроков...")

    game = Game()

    for _ in range(2):
        conn, addr = server.accept()
        player = game.add_player(conn, addr)
        print(f"Игрок {player.id + 1} подключен: {addr}")
        player.send_message(f"Вы игрок {player.id + 1}. Ожидаем второго игрока...")
        player.send_message 

    game.run()
    server.close()


if __name__ == "__main__":
    start_server()
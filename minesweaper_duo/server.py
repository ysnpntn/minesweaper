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
        self.hits_received = set()
        self.opponent = None
        self.lock = threading.Lock()
        self.game_over = False
        self.ready = False

    def send_message(self, message):
        try:
            self.conn.send((message + "\n").encode())
        except:
            self.game_over = True

    def receive_message(self):
        try:
            data = self.conn.recv(1024).decode().strip()
            return data
        except:
            self.game_over = True
            return ""


class Game:
    def __init__(self):
        self.players = []
        self.lock = threading.Lock()
        self.game_started = threading.Event()

    def add_player(self, conn, addr):
        with self.lock:
            player_id = len(self.players)
            player = Player(conn, addr, player_id)
            self.players.append(player)

            if player_id == 1:
                self.players[0].opponent = self.players[1]
                self.players[1].opponent = self.players[0]
                for p in self.players:
                    p.send_message("Оба игрока подключены! Начинаем расстановку мин.")
        return player

    def setup_mines(self, player):
        mines_received = 0

        while mines_received < MINES_COUNT and not player.game_over:
            player.send_message(f"Мина {mines_received + 1}/{MINES_COUNT}. Введите координаты X Y (0-4):")

            data = player.receive_message()
            if not data:
                continue

            try:
                x, y = map(int, data.split())
                if not (0 <= x < FIELD_SIZE and 0 <= y < FIELD_SIZE):
                    player.send_message("Ошибка: координаты должны быть от 0 до 4!")
                    continue

                if (x, y) in player.mines:
                    player.send_message("Ошибка: здесь уже есть мина!")
                    continue

                player.mines.add((x, y))
                mines_received += 1
                player.send_message(f"Установлена мина на ({x}, {y}). Осталось {MINES_COUNT - mines_received}")

            except ValueError:
                player.send_message("Ошибка: введите два числа через пробел!")

        player.ready = True
        player.send_message("Все мины расставлены! Ожидаем готовности противника...")

        while not all(p.ready for p in self.players) and not player.game_over:
            pass

        if not player.game_over:
            player.send_message("Оба игрока готовы! Начинаем игру.")
            self.game_started.set()

    def handle_player(self, player):
        self.setup_mines(player)
        self.game_started.wait()

        while not player.game_over:
            player.send_message("Введите координаты для хода X Y (0-4):")

            data = player.receive_message()
            if not data:
                continue

            try:
                x, y = map(int, data.split())
                if not (0 <= x < FIELD_SIZE and 0 <= y < FIELD_SIZE):
                    player.send_message("Ошибка: координаты должны быть от 0 до 4!")
                    continue

                with player.lock:
                    if (x, y) in player.hits_received:
                        player.send_message("Данные координаты были введены вами ранее! Введите другие.")
                        continue

                    player.hits_received.add((x, y))

                    if (x, y) in player.opponent.mines:
                        # Мгновенное уведомление обоим игрокам
                        player.send_message(f"Вы подорвались на мине противника на координатах ({x}, {y})")
                        player.opponent.send_message(f"Противник нашел вашу мину на ({x}, {y})")

                        # Проверяем, нашел ли игрок ВСЕ мины противника
                        found_mines = [coord for coord in player.hits_received if coord in player.opponent.mines]
                        if len(found_mines) == MINES_COUNT:
                            player.send_message("Вы подорвались на всех минах противника. Вы проиграли.")
                            player.opponent.send_message("Оппонент подорвался на всех ваших минах. Вы победили.")
                            player.game_over = True
                            player.opponent.game_over = True
                            return
                    else:
                        player.send_message("На данной координате мины нет.")

            except ValueError:
                player.send_message("Ошибка! Введите два числа через пробел (например: 1 2).")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(2)
    print(f"Сервер запущен на {HOST}:{PORT}")

    game = Game()

    try:
        while True:
            conn, addr = server.accept()
            print(f"Подключение от {addr}")
            player = game.add_player(conn, addr)

            if len(game.players) == 2:
                threading.Thread(target=game.handle_player, args=(game.players[0],)).start()
                threading.Thread(target=game.handle_player, args=(game.players[1],)).start()

    finally:
        server.close()


if __name__ == "__main__":
    start_server()

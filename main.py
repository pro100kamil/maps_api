import os
import sys
from io import BytesIO
from math import cos, radians

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

WIDTH, HEIGHT = SCREEN_SIZE = 600, 450


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.lon, self.lat = 37.530887, 55.703118
        self.scale = 17  # текущий масштаб
        self.setGeometry(100, 100, *SCREEN_SIZE)
        self.setWindowTitle('Отображение карты')
        self.image = QLabel(self)
        self.pixmap = None
        self.image.move(0, 0)
        self.image.resize(600, 450)
        self.update_pixmap()

    def get_image(self) -> bytes:
        """Возвращает изображение (карту)"""
        map_params = {
            "ll": f"{self.lon},{self.lat}",
            "l": "map",
            "z": self.scale
        }

        map_api_server = "http://static-maps.yandex.ru/1.x/"
        response = requests.get(map_api_server, params=map_params)

        if not response:
            print(f"Ошибка выполнения запроса: {response.status_code} "
                  f"({response.reason})")
            sys.exit(1)
        return response.content

    def update_pixmap(self) -> None:
        """Обновляет изображение (карту)"""
        self.pixmap = QPixmap.fromImage(QImage.fromData(self.get_image()))
        self.image.setPixmap(self.pixmap)

    def keyPressEvent(self, event):
        # изменение масштаба
        if event.key() == Qt.Key_Plus:
            print(self.scale)
            self.scale = min(self.scale + 1, 17)

        elif event.key() == Qt.Key_Minus:
            self.scale = max(self.scale - 1, 0)

        # Когда зум 17, то 1 градус широты равнялся 1206 пикселям. С уменьшением зума на 1,
        # уменьшалось это расстояния в пикселях на 1.104, но
        # Проблема в том, что оно уменьшается так до определенного момента,
        # с какого-то значения зума оно растет в геом прогрессиии
        elif event.key() == Qt.Key_Up:
            delta = (1 / 1206.943) * (1.104 ** (17 - self.scale)) * HEIGHT
            self.lat = min(85, self.lat + delta)
        elif event.key() == Qt.Key_Down:
            delta = (1 / 1206.943) * (1.104 ** (17 - self.scale)) * HEIGHT
            # Края карты определяются разным зумом, и они всегда разные, я пока взял константой -85
            self.lat = max(-85, self.lat - delta)
        elif event.key() == Qt.Key_Left:
            # Была формула где 1 градус долготы = 111 км * cos(широты).
            # Я просто взял 111 км за пиксели и перемножил с косинусом
            delta = (1 / 1206.943) * (1.104 ** (17 - self.scale)) * WIDTH * cos(radians(self.lat))
            self.lon = max(-175, self.lon - delta)
        self.update_pixmap()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wind = Window()
    wind.show()
    sys.exit(app.exec())

import os
import sys
from io import BytesIO

import requests
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QWidget, QLabel

SCREEN_SIZE = 600, 450


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, *SCREEN_SIZE)
        self.setWindowTitle('Отображение карты')
        self.pixmap = QPixmap.fromImage(QImage.fromData(self.get_image()))
        self.image = QLabel(self)
        self.image.move(0, 0)
        self.image.resize(600, 450)
        self.image.setPixmap(self.pixmap)

    def get_image(self) -> bytes:
        """Возвращает изображение (карту)"""
        map_params = {
            "ll": "37.530887,55.703118",
            "l": "map",
            "z": "17"
        }

        map_api_server = "http://static-maps.yandex.ru/1.x/"
        response = requests.get(map_api_server, params=map_params)
        if not response:
            print(f"Ошибка выполнения запроса: {response.status_code} "
                  f"({response.reason})")
            sys.exit(1)
        return response.content


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wind = Window()
    wind.show()
    sys.exit(app.exec())
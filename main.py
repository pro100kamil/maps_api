import os
import sys
from io import BytesIO
from PIL import Image

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi

WIDTH, HEIGHT = MAP_SIZE = 600, 450


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        loadUi('main.ui', self)

        self.lon, self.lat = 37.530887, 55.703118  # долгота и широта
        self.scale = 14  # текущий масштаб
        self.map_type = 'map'  # тип карты
        self.pt = None  # текущая метка

        self.map_file = "map.png"  # файл с картой

        self.pixmap = None
        self.address = None

        self.types_of_map.buttonToggled.connect(self.get_type_of_map)
        self.search_btn.clicked.connect(self.search_toponym)
        self.reset_btn.clicked.connect(self.reset_search)

        self.update_pixmap()

    def get_type_of_map(self, button):
        """Получение типа карты"""

        types = {-2: 'sat', -3: 'map',
                 -4: 'sat,skl'}  # Id кнопок в группе кнопок, текст кнопок
        # нежелательно использовать, так как его в дизайнере могут изменить

        if button.isChecked():
            self.map_type = types[self.types_of_map.id(button)]

            self.update_pixmap()

    def get_image(self) -> bytes:
        """Возвращает изображение (карту)"""

        map_params = {
            "ll": f"{self.lon},{self.lat}",
            "z": self.scale,
            "size": "650,450",
            "pt": self.pt,
            "l": self.map_type
        }

        map_api_server = "http://static-maps.yandex.ru/1.x/"
        response = requests.get(map_api_server, params=map_params)

        if not response:
            print(f"Ошибка выполнения запроса: {response.status_code} "
                  f"({response.reason})")
            sys.exit(1)

        return response.content

    def search_toponym(self) -> None:
        """Поиск топонима по нажатию кнопки поиска"""

        self.show_message()

        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

        geocoder_params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            "geocode": self.input_toponym.text(),
            "format": "json"
        }

        response = requests.get(geocoder_api_server, params=geocoder_params)
        if not response:
            self.reset_search()
            self.show_message(msg='Ошибка запроса!',
                              style='color: white; background-color: red; font-size: 20pt;')
            return

        variants = response.json()["response"]["GeoObjectCollection"]["featureMember"]

        if not variants:
            self.reset_search()
            self.show_message(msg='Ничего не найдено!',
                              style='color: white; background-color: red; font-size: 20pt;')
            return

        toponym = variants[0]

        self.lon, self.lat = tuple(
            map(float, toponym["GeoObject"]["Point"]["pos"].split()))
        self.pt = f"{self.lon},{self.lat},pm2rdl"
        self.address = toponym['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']

        self.show_message(msg=self.address,
                          style='color: white; background-color: green; font-size: 11pt;')

        self.update_pixmap()

    def update_pixmap(self) -> None:
        """Обновляет изображение (карту)"""

        image = Image.open(BytesIO(self.get_image()))
        image.save(self.map_file)
        self.pixmap = QPixmap(self.map_file)
        self.image.setPixmap(self.pixmap)
        self.image.setFocus()

    def keyPressEvent(self, event):
        # изменение масштаба
        if event.key() == Qt.Key_PageUp:
            self.scale = min(self.scale + 1, 17)
        elif event.key() == Qt.Key_PageDown:
            self.scale = max(self.scale - 1, 0)
        # перемещение центра карты
        elif event.key() == Qt.Key_Up:
            delta = 180 / (2 ** self.scale) * HEIGHT / 256
            self.lat = min(90 - delta / 2, self.lat + delta)
        elif event.key() == Qt.Key_Down:
            delta = 180 / (2 ** self.scale) * HEIGHT / 256
            self.lat = max(-90, self.lat - delta)
        elif event.key() == Qt.Key_Left:
            delta = 360 / (2 ** self.scale) * WIDTH / 256
            self.lon = max(-180, self.lon - delta)
        elif event.key() == Qt.Key_Right:
            delta = 360 / (2 ** self.scale) * WIDTH / 256
            self.lon = min(180, self.lon + delta)
        else:
            return
        self.update_pixmap()

    def closeEvent(self, event):
        """При закрытии формы удаляем файл с картой"""

        os.remove(self.map_file)

    def show_message(self, msg='', style=''):
        """Уведомление об ошибках или успешном поиске в статус-меню"""

        self.statusBar().showMessage(msg)
        self.statusBar().setStyleSheet(style)

    def reset_search(self):
        """Сброс поиска"""

        self.pt, self.address = '', ''
        self.show_message()
        self.update_pixmap()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    wind = Window()
    wind.show()
    sys.exit(app.exec())

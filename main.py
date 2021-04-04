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
        self.address = None
        self.index = None
        self.map_file = "map.png"  # файл с картой

        self.pixmap = None

        self.types_of_map.buttonToggled.connect(self.get_type_of_map)
        self.search_btn.clicked.connect(lambda text: self.search_toponym(geocode=self.input_toponym.text()))
        self.reset_btn.clicked.connect(self.reset_search)
        self.post_code.stateChanged.connect(self.change_state_post_code)

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

    def search_toponym(self, geocode, mode=1) -> None:
        """Поиск топонима по нажатию кнопки поиска"""

        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

        geocoder_params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            "geocode": geocode,
            "format": "json",
        }

        response = requests.get(geocoder_api_server, params=geocoder_params)
        if not response:
            self.reset_search()
            self.show_message(msg='Ошибка запроса!',
                              style='color: white; background-color: red;'
                                    ' font-size: 20pt;')
            return

        variants = response.json()["response"]["GeoObjectCollection"][
            "featureMember"]

        if not variants:
            self.reset_search()
            self.show_message(msg='Ничего не найдено!',
                              style='color: white; background-color: red; '
                                    'font-size: 20pt;')
            return

        toponym = variants[0]

        if mode:
            self.lon, self.lat = tuple(
                map(float, toponym["GeoObject"]["Point"]["pos"].split()))
            self.pt = f"{self.lon},{self.lat},pm2rdl"
        self.address = toponym['GeoObject']['metaDataProperty'][
            'GeocoderMetaData']['text']

        post_code = toponym['GeoObject']['metaDataProperty'][
            "GeocoderMetaData"]["Address"].get("postal_code")

        self.show_message(
            msg=self.address + ', индекс ' + post_code
            if self.post_code.isChecked() and post_code is not None
            else self.address,
            style='color: white; background-color: green; '
                  'font-size: 10pt; text-align: center;')

        self.update_pixmap()

    def update_pixmap(self) -> None:
        """Обновляет изображение (карту)"""

        image = Image.open(BytesIO(self.get_image()))
        image.save(self.map_file)
        self.pixmap = QPixmap(self.map_file)
        self.image.setPixmap(self.pixmap)
        self.image.setFocus()

    def change_state_post_code(self):
        """Обработка нажатия на checkbox"""

        if self.address is not None:
            self.search_toponym(self.address, mode=0)

    def keyPressEvent(self, event):
        # изменение масштаба
        if event.key() == Qt.Key_Equal:
            self.scale = min(self.scale + 1, 17)
        elif event.key() == Qt.Key_Minus:
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

    def mousePressEvent(self, event):
        l_x, l_y = self.image.x(), self.image.y()
        l_w, l_h = self.image.width(), self.image.height()
        if l_x <= event.x() <= l_x + self.image.width() and l_y < event.y() < l_y + self.image.height():
            d_x_px, d_y_px = event.x() - l_x - l_w / 2, -(event.y() - l_y - l_h / 2)
            d_x_degree = 360 / (2 ** self.scale) * d_x_px / 256
            d_y_degree = 180 / (2 ** self.scale) * d_y_px / 256
            coords = f'{self.lon + d_x_degree},{self.lat + d_y_degree}'
            self.pt = coords + ',pm2rdl'
            self.search_toponym(geocode=coords, mode=0)

    def closeEvent(self, event):
        """При закрытии формы удаляем файл с картой"""

        os.remove(self.map_file)

    def show_message(self, msg='', style='') -> None:
        """Уведомление об ошибках или успешном поиске в статус-меню"""

        self.statusBar().showMessage(msg)
        self.statusBar().setStyleSheet(style)

    def reset_search(self) -> None:
        """Сброс поиска"""

        self.pt, self.address = None, None
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

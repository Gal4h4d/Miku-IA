
import win32gui
import ctypes.wintypes
import pygame

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu, QAction
from PyQt5.QtGui import QMovie, QTransform
from PyQt5.QtCore import Qt, QPoint, QSize, QTimer


def obtener_rect_barra_tareas():
    hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
    if hwnd:
        rect = win32gui.GetWindowRect(hwnd)
        return rect
    else:
        return (0, 0, 0, 0)


class Funciones(QWidget):
    def __init__(self, asistente):
        super().__init__()
        self.asistente = asistente

        pygame.mixer.init()

        self.movie_sostenida = QMovie("static/img/miku_sostenida.gif")
        self.movie_sostenida.setScaledSize(QSize(350, 350))

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel(self)

        self.movie_normal = QMovie("static/img/miku.gif")
        self.movie_normal.setScaledSize(QSize(350, 350))

        self.movie = self.movie_normal
        self.label.setMovie(self.movie)
        self.label.setFixedSize(350, 350)

        self.movie_caida = QMovie("static/img/miku_caida.gif")
        self.movie_caida.setScaledSize(QSize(350, 350))

        self.volteado = True

        self.movie.frameChanged.connect(self.actualizar_frame)
        self.movie.start()

        self.resize(350, 350)

        pantalla = QApplication.primaryScreen().geometry()
        rect_barra = obtener_rect_barra_tareas()
        left, top, right, bottom = rect_barra

        start_x = pantalla.left()
        start_y = top - self.height() + 95

        self.pos_base_y = start_y

        self.timer_gravedad = QTimer()
        self.timer_gravedad.timeout.connect(self.caer)

        self.move(start_x, start_y)

        self.ruta = [
            QPoint(start_x, start_y),
            QPoint(pantalla.right() - self.width(), start_y),
        ]
        self.indice_ruta = 0
        self.velocidad = 5

        self.direccion_actual = "derecha"

        self.timer = QTimer()
        self.timer.timeout.connect(self.mover_en_ruta)
        self.timer.start(50)

        self.moving = False
        self.offset = QPoint()

        self.show()

    def actualizar_frame(self):
        frame = self.movie.currentPixmap()
        if self.volteado:
            transform = QTransform().scale(-1, 1)
            frame = frame.transformed(transform)
        self.label.setPixmap(frame)

    def mover_en_ruta(self):
        destino = self.ruta[self.indice_ruta]
        pos_actual = self.pos()

        dx = destino.x() - pos_actual.x()
        dy = destino.y() - pos_actual.y()
        distancia = (dx ** 2 + dy ** 2) ** 0.5

        if distancia < self.velocidad:
            self.move(destino)
            self.indice_ruta = (self.indice_ruta + 1) % len(self.ruta)
        else:
            nx = pos_actual.x() + self.velocidad * dx / distancia
            ny = pos_actual.y() + self.velocidad * dy / distancia
            self.move(int(nx), int(ny))

            if dx > 0 and self.direccion_actual != "derecha":
                self.volteado = True
                self.direccion_actual = "derecha"
            elif dx < 0 and self.direccion_actual != "izquierda":
                self.volteado = False
                self.direccion_actual = "izquierda"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.moving = True
            self.offset = event.pos()
            self.timer.stop()
            self.cambiar_animacion(self.movie_sostenida)
        elif event.button() == Qt.RightButton:
            menu = QMenu(self)
           
            accion_crear_carpeta = QAction("📁 Crear carpeta", self)
            accion_crear_carpeta.triggered.connect(self.asistente.crear_carpeta)

            accion_abrir_google = QAction("🌐 Abrir Google", self)
            accion_abrir_google.triggered.connect(self.asistente.abrir_google)

            accion_escuchar = QAction("🎤 Escuchar", self)
            accion_escuchar.triggered.connect(self.asistente.escuchar_microfono)


            menu.addAction(accion_escuchar)
            menu.addAction(accion_crear_carpeta)
            menu.addAction(accion_abrir_google)

            menu.exec_(event.globalPos())

    def mouseMoveEvent(self, event):
        if self.moving:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.moving = False

        if self.y() < self.pos_base_y:
            self.timer_gravedad.start(30)
            self.cambiar_animacion(self.movie_caida)
        else:
            self.cambiar_animacion(self.movie_normal)
            self.timer.start(50)

    def caer(self):
        y_actual = self.y()
        if y_actual < self.pos_base_y:
            self.move(self.x(), y_actual + 10)
        else:
            self.timer_gravedad.stop()
            self.move(self.x(), self.pos_base_y)
            self.cambiar_animacion(self.movie_normal)
            self.timer.start(50)

    def cambiar_animacion(self, nueva_movie):
        self.movie.frameChanged.disconnect(self.actualizar_frame)
        self.movie.stop()
        self.movie = nueva_movie
        self.label.setMovie(self.movie)
        self.movie.frameChanged.connect(self.actualizar_frame)
        self.movie.start()

    @staticmethod
    def obtener_ruta_escritorio():
        SHGFP_TYPE_CURRENT = 0
        CSIDL_DESKTOP = 0

        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, SHGFP_TYPE_CURRENT, buf)
        return buf.value
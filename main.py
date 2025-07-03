import sys
import asyncio

from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop

from IA import Asistente
from funcionality import Funciones  

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    asistente = Asistente()
    funciones = Funciones(asistente) 

    with loop:
        loop.run_forever()


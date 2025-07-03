from PyQt5.QtWidgets import QWidget
from qasync import asyncSlot

import os
import webbrowser
import asyncio
import edge_tts
import pygame
import speech_recognition as sr
import aiohttp 
import uuid

class Asistente(QWidget):
    @asyncSlot()
    async def crear_carpeta(self):
        escritorio = self.obtener_ruta_escritorio()
        nombre_carpeta = "Nueva Carpeta de Miku"
        ruta = os.path.join(escritorio, nombre_carpeta)
        os.makedirs(ruta, exist_ok=True)
        print(f"Carpeta creada en: {ruta}")
        await self.hablar("He creado una carpeta nueva en tu escritorio.")

    @asyncSlot()
    async def abrir_google(self):
        webbrowser.open("https://www.google.com")
        await self.hablar("Abriendo Google para ti.")

    async def hablar(self, texto):
        nombre_archivo = f"voz_{uuid.uuid4()}.mp3"
        ruta_voz = os.path.join(os.path.expanduser("~"), nombre_archivo)

        # Generar nuevo audio
        tts = edge_tts.Communicate(texto, voice="es-ES-ElviraNeural")

        await tts.save(ruta_voz)

        # Reproducir audio
        pygame.mixer.music.load(ruta_voz)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

        pygame.mixer.music.stop()

        # Intentar eliminar varias veces
        import time
        for intento in range(10):
            try:
                os.remove(ruta_voz)
                break
            except PermissionError:
                await asyncio.sleep(0.2)
        else:
            print(f"No se pudo eliminar {ruta_voz} después de reproducirlo.")


    @asyncSlot()
    async def escuchar_microfono(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            await self.hablar("Te estoy escuchando...")
            audio = recognizer.listen(source)

        try:
            texto = recognizer.recognize_google(audio, language="es-ES")
            print("Escuché:", texto)
            respuesta = await self.enviar_a_ia(texto)
            await self.hablar(respuesta)
        except sr.UnknownValueError:
            await self.hablar("No entendí lo que dijiste.")
        except sr.RequestError:
            await self.hablar("Hubo un problema con el servicio de reconocimiento.")

    async def enviar_a_ia(self, mensaje):
        token = "Token"  # Pon aquí tu token de Ia pos la API
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": mensaje}]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data) as response:
                if response.status == 200:
                    resultado = await response.json()
                    return resultado["choices"][0]["message"]["content"]
                elif response.status == 401:
                    return "Error 401: No autorizado. Revisa tu clave API."
                else:
                    return f"Error {response.status}: Hubo un problema al conectar con la inteligencia artificial."

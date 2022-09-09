import asyncio
import sys
from enum import Enum

import websockets
import requests
import time
import json
import nest_asyncio

from pypresence import Presence

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

nest_asyncio.apply()

base_url = "https://mp3.zing.vn"


def duration_to_mill(duration): return duration * 1000


def get_zing_song_data(data):
    key_path = data['key_path']

    if 'video' in key_path:
        key_path = key_path.replace('video', 'audio')

    with requests.get(f'{base_url}/xhr{key_path}') as req:
        res = req.json()

        song_data = {}
        if 'album' in key_path:
            for song in res['data']['items']:
                if data['song_title'] == (
                        song['name'] or song['title'] or song['album']['name'] or song['album']['title']):
                    song_data = song
                    break
        else:
            song_data = res['data']

        return song_data


class Status(Enum):
    Online = 0
    Offline = 1


class Server(QObject):
    finished = pyqtSignal()
    data = pyqtSignal(dict)
    status = pyqtSignal(Status)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port

        self.loop = asyncio.get_event_loop()

        self.start_server = websockets.serve(self.echo, self.host, self.port, loop=self.loop)

    async def echo(self, websocket):
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(data)
                    if 'isConnected' in data:
                        if data['isConnected']:
                            self.status.emit(Status.Online)
                    else:
                        self.data.emit(data)

                except json.JSONDecodeError:
                    print('decode error!')
                except AttributeError:
                    print('no key has found!')
                except requests.HTTPError:
                    print('request error!')
        finally:
            self.status.emit(Status.Offline)
            print('connection closed!')

    def run_server(self):
        try:
            self.loop.run_until_complete(self.start_server)
            print('server started!')
            self.loop.run_forever()
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()
            self.finished.emit()

    def stop_event_loop(self):
        self.loop.close()


class ZingMPre:
    def __init__(self):
        self.config = {
            'client_id': 997427282606047282,
            'icon': 'assets/logo600.png',
            'app_version_info': f'ZingMPre v{1.3}',
            'status_bar': {
                'status': f'Extension - {Status.Offline.name}',
            },
            'about_button': 'About',
            'quit_button': 'Quit'
        }

        self.RPC = Presence(self.config['client_id'])

        # Threading server
        self.thread = QThread()
        self.server = Server('localhost', 8765)

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.menu = QMenu()
        self.tray = QSystemTrayIcon()

        # Create the icon
        icon = QIcon(self.config['icon'])

        # Create the tray
        self.tray.setIcon(icon)
        self.tray.setVisible(True)

        # Create the menu
        # Version bar
        self.version_bar = QAction(self.config['app_version_info'])
        self.version_bar.setIcon(icon)
        self.version_bar.setEnabled(False)
        self.menu.addAction(self.version_bar)

        # Info bar
        self.status_button = QAction(self.config['status_bar']['status'])
        self.status_button.setDisabled(True)
        self.menu.addAction(self.status_button)

        self.menu.addSeparator()

        # About bar
        self.about_button = QAction(self.config['about_button'])
        self.about_button.triggered.connect(self.on_about)
        self.menu.addAction(self.about_button)
        self.msg = QMessageBox()
        self.msg.setIcon(self.msg.Icon.Critical)
        self.msg.setWindowTitle('Information')
        self.msg.setText('About')
        self.msg.setInformativeText('author by @bad_kem')

        # Add a Quit option to the menu.
        self.quit_menu = QAction(self.config['quit_button'])
        self.quit_menu.triggered.connect(self.on_quit)
        self.menu.addAction(self.quit_menu)

        # Add the menu to the tray
        self.tray.setContextMenu(self.menu)

    def update_status(self, data):
        if data['playing']:
            song_data = {}
            try:
                res = get_zing_song_data(data)
                now = int(round((time.time() - data['currentTime']) * 1000))
                time_left = now + duration_to_mill(res['duration'])
                song_data.update({
                    "state": res['title'],
                    "details": res['artists_names'] or res['performer'] or 'Unknown',
                    "start": now,
                    "end": time_left,
                    "large_image": res['thumbnail'],
                    "small_image": 'logo600',
                    "buttons": [
                        {
                            "label": "Play on ZingMp3",
                            "url": f'{base_url}{res["link"]}'
                        }
                    ]
                })
            except requests.HTTPError:
                print('request error!')

            status = self.RPC.update(**song_data)
            print(status)
        else:
            self.RPC.clear()

    def update_status_bar(self, status: Status):
        self.status_button.setText(f'Extension - {status.name}')

    def on_about(self):
        self.msg.exec_()

    def on_quit(self):
        self.app.quit()

    def run_app(self):
        self.RPC.connect()

        # Move server to thread
        self.server.moveToThread(self.thread)

        # Connect signals and slots
        self.thread.started.connect(self.server.run_server)
        self.thread.finished.connect(self.thread.deleteLater)

        self.server.finished.connect(self.server.stop_event_loop)
        self.server.finished.connect(self.thread.quit)
        self.server.finished.connect(self.server.deleteLater)

        self.server.data.connect(self.update_status)
        self.server.status.connect(self.update_status_bar)

        # Start thread
        self.thread.start()

        sys.exit(self.app.exec())


if __name__ in '__main__':
    ZingMPre().run_app()

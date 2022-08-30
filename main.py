import asyncio
import websockets
import requests
import time
import json
import nest_asyncio

from pypresence import Presence

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

nest_asyncio.apply()

client_id = 997427282606047282

RPC = Presence(client_id)

RPC.connect()

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


def update_status(data):
    if data:
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

            status = RPC.update(**song_data)
            print(status)
        else:
            RPC.clear()


class ZingMPre:
    def __init__(self, host, port):
        self.config = {
            'icon': 'assets/logo600.png',
            'status_bar': {
                'status': 'offline',
            },
            'about_button': 'About',
            'quit_button': 'Quit'
        }
        self.host = host
        self.port = port
        self.qt_loop_task = asyncio.ensure_future(self.qt_loop())  # task will work alongside with the server
        self.loop = asyncio.get_event_loop()
        self.start_server = websockets.serve(self.echo, self.host, self.port, loop=self.loop)

        self.app = QApplication([])
        self.app.setQuitOnLastWindowClosed(False)

        self.menu = QMenu()
        self.tray = QSystemTrayIcon()

        # Create the icon
        icon = QIcon(self.config['icon'])

        # Create the tray
        self.tray.setIcon(icon)
        self.tray.setVisible(True)

        # Create the menu
        self.status_button = QAction(self.config['status_bar']['status'])
        self.status_button.setIcon(icon)
        self.status_button.setDisabled(True)
        self.menu.addAction(self.status_button)

        self.about_button = QAction(self.config['about_button'])
        self.about_button.triggered.connect(self.on_about)
        self.menu.addAction(self.about_button)
        # for about action
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

    def update_status_bar(self, status):
        self.status_button.setText(status)

    def on_about(self):
        self.msg.exec_()

    def on_quit(self):
        self.loop.stop()
        self.app.quit()

    async def echo(self, websocket):
        try:
            message = await websocket.recv()
            print(message)
            try:
                update_status(json.loads(message))
            except json.JSONDecodeError:
                print('decode error!')
            except AttributeError:
                print('no key has found!')
            except requests.HTTPError:
                print('request error!')
        except websockets.ConnectionClosed:
            print('connection closed!')

    async def qt_loop(self):
        while 1:
            self.app.processEvents()  # allow Qt loop to work a bit
            await asyncio.sleep(0.01)  # allow asyncio loop to work a bit

    def run_app(self):
        try:
            self.loop.run_until_complete(self.start_server)
            print('started server!')
            self.loop.run_forever()
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()


if __name__ in '__main__':
    zm = ZingMPre('localhost', 8765)
    zm.run_app()

# # This is a sample Python script.
#
# # Press ⌃R to execute it or replace it with your code.
# # Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
#
#
# def print_hi(name):
#     # Use a breakpoint in the code line below to debug your script.
#     print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.
#
#
# # Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     print_hi('PyCharm')
#
# # See PyCharm help at https://www.jetbrains.com/help/pycharm/

import asyncio
import websockets
import requests
import time

from pypresence import Presence

HOST = "localhost"
PORT = 8765

base_url = "https://mp3.zing.vn/xhr/media/get-source?type=audio&key="

client_id = "997427282606047282"


def song_url(key):
    return f'{base_url}{key}'


def get_zing_song_data():
    with requests.get(song_url("ZHxmyZmsdJXCcNhyGyFGLmTZgQNJiLpWp")) as req:
        res = req.json()
        data = res['data']
        print(data)
        return {"state": data['title'], "details": data['artists_names']}


def start():
    rpc = Presence(client_id)
    rpc.connect()

    while 1:
        data = get_zing_song_data()
        stt = rpc.update(**data)
        print(stt)
        time.sleep(15)


async def receive(websocket):
    async for message in websocket:
        print(message)
        # await websocket.send(message)


async def main():
    async with websockets.serve(receive, HOST, PORT):
        await asyncio.Future()  # run forever


if __name__ in '__main__':
    asyncio.run(main())

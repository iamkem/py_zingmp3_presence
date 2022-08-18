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
import json
import nest_asyncio

from pypresence import Presence

nest_asyncio.apply()

client_id = 997427282606047282

RPC = Presence(client_id)

HOST = "localhost"
PORT = 8765

base_url = "https://mp3.zing.vn"


def song_url(key):
    return f'{base_url}/xhr/media/get-source?type=audio&key={key}'


def get_zing_song_data(key):
    with requests.get(song_url(key)) as req:
        res = req.json()
        data = res['data']
        return {"state": data['title'], "details": data['artists_names']}


def start_rpc(data):
    RPC.connect()

    stt = RPC.update(**data, large_image='logo600')
    print(stt)


def cancel_prc():
    RPC.close()


async def echo(websocket):
    async for message in websocket:
        try:
            data = json.loads(message)
            if data['playing']:
                print('playing')
                song_data = get_zing_song_data(data['key'])
                start_rpc(song_data)
            else:
                print('not playing')
                cancel_prc()

        except json.JSONDecodeError:
            print('decode error!')
        except AttributeError:
            print('no key has found!')
        except requests.HTTPError:
            print('request error!')


async def main():
    async with websockets.serve(echo, HOST, PORT):
        await asyncio.Future()


if __name__ in '__main__':
    asyncio.run(main())

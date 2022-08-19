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

RPC.connect()


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
                if data['song_title'] == (song['name'] or song['title'] or song['album']['name'] or song['album']['title']):
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


async def echo(websocket):
    async for message in websocket:
        try:
            update_status(json.loads(message))
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

import asyncio
import json
from datetime import datetime
import os
import random
from time import time
from typing import Any
from urllib.parse import unquote, quote, parse_qs

import aiohttp
import logger

from random import randint
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw import types
from pyrogram.raw.functions.messages import RequestAppWebView

from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy

from .headers import headers

class Tapper:

    def __init__(self, tg_client: Client):
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.start_param = ''
        self.locale = 'en'
        self.is_premium = False
        self.session_id = None
        self.tg_id = None
        self.proxy = None
        self.last_event_time = None

async def get_tg_web_data(self, peer_id: str, short_name: str, start_param: str) -> str:
        if self.proxy:
            proxy = Proxy.from_str(self.proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()

                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            peer = await self.tg_client.resolve_peer(peer_id)
            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                platform='android',
                app=types.InputBotAppShortName(bot_id=peer, short_name=short_name),
                write_allowed=True,
                start_param=start_param
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
            query_params = parse_qs(tg_web_data)
            user_data = query_params.get('user')[0]
            auth_date = query_params.get('auth_date')[0]
            hash_value = query_params.get('hash')[0]
            chat_instance = query_params.get('chat_instance')
            chat_type = query_params.get('chat_type')
            start_param = query_params.get('start_param')
            user_data_encoded = quote(str(user_data))
            if peer_id == 'notpixel':
                user_json = json.loads(user_data)
                self.start_param = start_param
                self.tg_id = user_json.get('id')
                self.locale = user_json.get('language_code')
                self.is_premium = user_json.get('is_premium') is not None

            chat_param = f'&chat_instance={chat_instance[0]}&chat_type={chat_type[0]}' \
                if chat_instance and chat_type else ''
            start_param = f'&start_param={start_param[0]}' if start_param else ''
            init_data = ''.join(
                [f"user={user_data_encoded}", chat_param, start_param, f'&auth_date={auth_date}&hash={hash_value}'])

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return init_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def auth_in_nuts(self, http_client: aiohttp.ClientSession, retry=0):
        try:
            http_client.headers = headers
            get_auth_token = await http_client.post(f'https://nutsfarm.crypton.xyz/api/v1/auth/token')
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error sending game event: {error}")
            await asyncio.sleep(delay=randint(3, 7))

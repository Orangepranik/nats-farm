import random
import aiohttp
import json

from aiohttp_proxy import ProxyConnector
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered

from bot.core.headers import headers

from better_proxy import Proxy

from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw import types

from urllib.parse import unquote, quote, parse_qs

from bot.utils.accounts import Accounts

from bot.core.auth import get_tg_client

import logger

import asyncio


class Tapper: 

    def __init__(self, tg_client: Client):
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.locale = 'en'
        self.is_premium = None
        self.session_id = None
        self.proxy = None
        self.start_param = ''

    async def login_in_bot(self):
        print('a')

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://ipinfo.io/ip', timeout=aiohttp.ClientTimeout(10))
            ip = (await response.text())
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def create_acc_in_bot(self, http_client: aiohttp.ClientSession, init_data: str):
        """
            - init_data web-user data телеграмма, для авторизации пользователя в веб
        """
        response = await http_client.get(f"https://nutsfarm.crypton.xyz/")
        response.raise_for_status()
        http_client.headers['Referer'] = f'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
        payload = {'authData': init_data}   
        payload['language'] = 'RU'
        payload['referralCode'] = 'ATADFYOPHBQFOSV'
        del http_client.headers['X-Requested-With']
        response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/auth/register', json=payload, 
                                                    timeout=aiohttp.ClientTimeout(60))
        response_json = await response_auth_token.json()
        tokens = await self.claim_start_bonus(http_client=http_client, init_data=init_data, json_auth=response_json)  
        return tokens    

    async def get_auth_token_static(self, http_client: aiohttp.ClientSession, refresh_token: str):
        """
            Берёт токен авторизации, который после будет использоваться для подачи запросов пользователю на сервер nuts
            - Живёт 24 часа
        """
        payload = {'refreshToken': refresh_token}
        response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/auth/token', json=payload, 
                                                    timeout=aiohttp.ClientTimeout(60))
        response_json = await response_auth_token.json()
        return response_json

    async def login_in_bot_1(self, http_client: aiohttp.ClientSession, init_data: str):
        http_client.headers['Referer'] = 'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
        http_client.headers['authority'] = 'nutsfarm.crypton.xyz'
        del http_client.headers['Connection']
        http_client.headers['Accept-Language'] = 'ru-RU,ru;q=0.9,en-US;q=0.8;q=0.7'
        http_client.headers['Content-Type'] = 'text/plain;charset=UTF-8'
        response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/auth/login', data=f'{init_data}', 
                                                    timeout=aiohttp.ClientTimeout(60))
        response_json = await response_auth_token.json()
        del http_client.headers['Content-Type']
        return response_json

    async def claim_start_bonus(self, http_client: aiohttp.ClientSession, init_data: str, json_auth):
        """
                - init_data web-user data телеграмма, для авторизации пользователя в веб
                - json_auth - ACCES TOKEN для клейма старт бонуса
            После регистрации пользователя собирает start_bonus который даёт 1337 токенов, вылазит только 1 раз
            return 
            - refresh_token
            - access_token
        """
        http_client.headers['Referer'] = f'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
        text = f"Bearer {json_auth['accessToken']}"
        http_client.headers['Authorization'] = text
        claim = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/farming/startBonus', 
                                                    timeout=aiohttp.ClientTimeout(60))
        token_forever = await self.get_auth_token_static(http_client=http_client, refresh_token=json_auth['refreshToken'])
        logged_in_bot = await self.login_in_bot_1(http_client=http_client, init_data=init_data)
        http_client.headers['Accept-Language'] = 'ru-RU,ru;q=0.9,en-US;q=0.8;q=0.7'
        await self.claim_dayly_bonus(http_client=http_client, acces_token=logged_in_bot['accessToken'])
        await self.start_farm(http_client=http_client, acces_token=logged_in_bot['accessToken'])
        return {"refresh_token": json_auth['refreshToken'], "access_token": logged_in_bot['accessToken']}

    async def claim_dayly_bonus(self, http_client: aiohttp.ClientSession, acces_token: str):
        text = f"Bearer {acces_token}"
        http_client.headers['Authorization'] = text
        claim = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/streak/current/claim?timezone=Europe/Kiev&payForFreeze=true',    
                                                        timeout=aiohttp.ClientTimeout(60))


    async def start_farm(self, http_client: aiohttp.ClientSession, acces_token: str):
        text = "Bearer {acces_token}"
        http_client.headers['Authorization'] = text
        response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/farming/farm', 
                                                    timeout=aiohttp.ClientTimeout(60))
        CURRENT_FARM_INFO = await http_client.get(f"https://nutsfarm.crypton.xyz/api/v1/farming/current")


    async def get_tg_web_view(self, tg_client: Client, proxy: str):
        proxy = Proxy.from_str(proxy)
        proxy_dict = dict(
                    scheme=proxy.protocol,
                    hostname=proxy.host,
                    port=proxy.port,
                    username=proxy.login,
                    password=proxy.password
                )
        tg_client.proxy = proxy_dict
        peer = await tg_client.resolve_peer('nutsfarm_bot')
        web_view = await tg_client.invoke(RequestAppWebView(
            peer=peer,
            platform='android',
            app=types.InputBotAppShortName(bot_id=peer, short_name='nutscoin'),
            write_allowed=True,
            start_param='ref_ATADFYOPHBQFOSV'))
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
        user_json = json.loads(user_data)
        _start_param = start_param
        _tg_id = user_json.get('id')
        _locale = user_json.get('language_code')
        _is_premium = user_json.get('is_premium') is not None
        chat_param = f'&chat_instance={chat_instance[0]}&chat_type={chat_type[0]}' \
            if chat_instance and chat_type else ''
        start_param = f'&start_param={start_param[0]}' if start_param else ''
        init_data = ''.join(
            [f"user={user_data_encoded}", chat_param, start_param, f'&auth_date={auth_date}&hash={hash_value}'])
        return init_data


    async def run(self, user_agent: str, proxy: str, new_bot_user: bool, session_name: str):
        self.proxy = proxy
        s = proxy.split(":")
        proxy_connection = ProxyConnector().from_url(f"{s[0]}:{s[1]}:{s[2]}@{s[3]}:{s[4]}") if proxy else None
        headers['User-Agent'] = user_agent
        init_data = await self.get_tg_web_view(tg_client=self.tg_client, proxy=proxy)
        async with aiohttp.ClientSession(headers=headers, connector=proxy_connection) as http_client:
            if new_bot_user:
                tokens = await self.create_acc_in_bot(http_client=http_client, init_data=init_data)
                accs = await Accounts().edit_account(session_name=session_name, refresh_token=tokens.get('refresh_token'),
                                                     acces_token=tokens.get('access_token'))


async def run_tapper(tg_client: Client, user_agent: str, proxy: str, session_name: str):
    await Tapper(tg_client=tg_client).run(user_agent=user_agent, proxy=proxy, new_bot_user=True,
                                          session_name=session_name)


async def a():
    accs = await Accounts().get_accounts()
    for account in accs.get('unregistered_accs'):
        print(account.get('session_name'))
        await asyncio.sleep(random.randint(10, 60))
        print(account.get('session_name'))
        session = await get_tg_client(session_name=account.get('session_name'), proxy=account.get('proxy'))
        async with session:
            await run_tapper(tg_client=session, user_agent=account.get('user_agent'),
                            proxy=account.get('proxy'), session_name=account.get('session_name'))
            
asyncio.run(a())
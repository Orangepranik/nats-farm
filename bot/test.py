import asyncio
import json
from aiohttp_proxy import ProxyConnector
import aiohttp

from pyrogram import Client
from pyrogram.raw import types
from better_proxy import Proxy
from pyrogram.raw.functions.messages import RequestAppWebView

from core.auth import get_tg_client
from core.headers import headers
from core.tapper import Tapper

from urllib.parse import unquote, quote, parse_qs




proxy = 'http://FwgpGQ:AGsFNt:176.96.141.233:8000'

async def a(tg_client: Client, proxy: str):
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
    print(auth_url)
    print(unquote(auth_url))
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
    print(init_data)
    return init_data

async def aa():
    session = await get_tg_client(session_name='v#2', proxy=proxy)
    print(session)
    async with session:
        user_data = await session.get_me()
        print(user_data)
        init_data = await a(tg_client=session, proxy=proxy)

async def login_in_bot(http_client: aiohttp.ClientSession, init_data: str):
    http_client.headers['Referer'] = 'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
    http_client.headers['authority'] = 'nutsfarm.crypton.xyz'
    print('ХЕДЕРСЫ ЛОГИН В БОТ')
    del http_client.headers['Authorization']
    print(http_client.headers)
    response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/auth/login', json=init_data, 
                                                 timeout=aiohttp.ClientTimeout(60))
    print(f'ФУНКЦИЯ ЛОГИН В БОТА')
    print(response_auth_token.raise_for_status())
    print(response_auth_token.ATTRS)
    response_json = await response_auth_token.json()
    print(response_json)
    return response_json

async def get_auth_token_static(http_client: aiohttp.ClientSession, refresh_token: str):
    payload = {'refreshToken': refresh_token}
    response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/auth/token', json=payload, 
                                                 timeout=aiohttp.ClientTimeout(60))
    response_json = await response_auth_token.json()
    return response_json
    
async def create_acc_in_bot(http_client: aiohttp.ClientSession, init_data: str):
    response = await http_client.get(f"https://nutsfarm.crypton.xyz/")
    response.raise_for_status()
    http_client.headers['Referer'] = f'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
    payload = {'authData': init_data}   
    payload['language'] = 'RU'
    payload['referralCode'] = 'ATADFYOPHBQFOSV'
    del http_client.headers['X-Requested-With']
    print(http_client.headers)
    response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/auth/register', json=payload, 
                                                 timeout=aiohttp.ClientTimeout(60))
    
    print('responce_auth_token снизу')
    print(response_auth_token)
    print(response_auth_token.raise_for_status())
    response_json = await response_auth_token.json()
    print(response_json)
    print(response_json['accessToken'])
    await claim_start_bonus(http_client=http_client, init_data=init_data, json_auth=response_json)

async def claim_start_bonus(http_client: aiohttp.ClientSession, init_data: str, json_auth):
    payload = {'authData': init_data}  
    http_client.headers['Referer'] = f'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
    text = f"Bearer {json_auth['accessToken']}"
    http_client.headers['Authorization'] = text
    claim = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/farming/startBonus', 
                                                 timeout=aiohttp.ClientTimeout(60))
    print(claim.raise_for_status())
    print(await claim.text())
    token_forever = await get_auth_token_static(http_client=http_client, refresh_token=json_auth['refreshToken'])
    print("ЗДЕСЬ ИНИТ ДАТА")
    print(init_data)
    logged_in_bot = await login_in_bot(http_client=http_client, init_data=init_data)
    await claim_dayly_bonus(http_client=http_client, acces_token=logged_in_bot['accessToken'])
    await start_farm(http_client=http_client, acces_token=logged_in_bot['accessToken'])

async def claim_dayly_bonus(http_client: aiohttp.ClientSession, acces_token: str):
    text = f"Bearer {acces_token}"
    http_client.headers['Authorization'] = text
    claim = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/streak/current/claim?timezone=Europe/Kiev&payForFreeze=true',    
                                                    timeout=aiohttp.ClientTimeout(60))
    print(await claim.text())

async def start_farm(http_client: aiohttp.ClientSession, acces_token: str):
    text = "Bearer {acces_token}"
    http_client.headers['Authorization'] = text
    response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/farming/farm', 
                                                timeout=aiohttp.ClientTimeout(60))
    print(await response_auth_token.text())
    CURRENT_FARM_INFO = await http_client.get(f"https://nutsfarm.crypton.xyz/api/v1/farming/current")
    print(await CURRENT_FARM_INFO.json())

async def get_current_farm_info(http_client: aiohttp.ClientSession, acces_token: str):
    http_client.headers['Referer'] = f'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
    text = "Bearer eyJhbGciOiJIUzM4NCJ9.eyJzdWIiOiI3OTU5MjYzNjkxIiwicm9sZXMiOiIiLCJqdGkiOiIxMDE2ODI0Njk2Mjg0ODM5OTM4IiwiZXhwIjoxNzMwMzg0MjcxfQ.w2vPQvowQ05c6U4k3WfAZrrbgP7M1wGI7hZ5ZEm7C0zYt1wti_shraxkAiRHZ5Iu"
    http_client.headers['Authorization'] = text
    CURRENT_FARM_INFO = await http_client.get(f"https://nutsfarm.crypton.xyz/api/v1/farming/current", 
                                                timeout=aiohttp.ClientTimeout(60))
    print(CURRENT_FARM_INFO.raise_for_status())
    print(await CURRENT_FARM_INFO.text())

async def rr():
    session = await get_tg_client(session_name='v#21', proxy=proxy)
    print(session)
    async with session:
        user_data = await session.get_me()
        print(user_data)
        init_data = await a(tg_client=session, proxy=proxy)
        proxy_s = 'http://FwgpGQ:AGsFNt@176.96.141.233:8000'
        proxy_conn = ProxyConnector().from_url(proxy_s) if proxy else None
        async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
            user_info = await create_acc_in_bot(http_client=http_client, init_data=init_data)
            await login_in_bot_1(http_client=http_client)

async def login_in_bot_1(http_client: aiohttp.ClientSession):
    http_client.headers['Referer'] = 'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
    http_client.headers['authority'] = 'nutsfarm.crypton.xyz'
    del http_client.headers['Connection']
    http_client.headers['Accept-Language'] = 'ru-RU,ru;q=0.9,en-US;q=0.8;q=0.7'
    http_client.headers['Content-Type'] = 'text/plain;charset=UTF-8'
    print('ХЕДЕРСЫ ЛОГИН В БОТ')
    print(http_client.headers)
    response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/auth/login', data='user=%7B%22id%22%3A8029291685%2C%22first_name%22%3A%22brat%20geni%22%2C%22last_name%22%3A%22%22%2C%22language_code%22%3A%22en%22%2C%22allows_write_to_pm%22%3Atrue%7D&chat_instance=-2302799849323426781&chat_type=sender&start_param=ref_ATADFYOPHBQFOSV&auth_date=1730389083&hash=ac49251f06710e6cb9c833084a4657c499ae039516ed93ded31d2cdcf3d2bafe', 
                                                 timeout=aiohttp.ClientTimeout(60))
    print(f'ФУНКЦИЯ ЛОГИН В БОТА')
    print(response_auth_token.raise_for_status())
    print(response_auth_token.ATTRS)
    response_json = await response_auth_token.json()
    print(response_json)
    return response_json

asyncio.run(rr())
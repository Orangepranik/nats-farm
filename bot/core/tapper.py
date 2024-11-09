import datetime
import random
from typing import Union
import aiohttp
import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
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


BALANCE = 0

class Tapper: 

    def __init__(self, tg_client: Client):
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.locale = 'en'
        self.is_premium = None
        self.session_id = None
        self.proxy = None
        self.access_token = None
        self.refresh_token = None
        self.init_data = None
        self.start_param = ''
        self.new_start_farm_time_date = None

    async def login_in_bot(self):
        print('a')

    async def get_info_claimed_daily_bonus(self, http_client: aiohttp.ClientSession, access_token: str):
        text = f"Bearer {access_token}"
        http_client.headers['Authorization'] = text
        del http_client.headers['Origin']
        http_client.headers['Referer'] = 'https://nutsfarm.crypton.xyz/'
        payload = {'timezone': 'Europe/Kiev'}
        info = await http_client.get(f"https://nutsfarm.crypton.xyz/api/v1/streak/current/info?timezone=Europe/Kiev", json=payload)
        resp = await info.json()
        print(resp)
        if resp.get('streakRewardReceivedToday') is False:
            await self.claim_dayly_bonus(http_client=http_client, acces_token=access_token)
        else:
            print('Daily bonus getted earlier')

    async def get_current_farming_status(self, http_client: aiohttp.ClientSession, acces_token: str):
        """
            Получает статус текущего фарма, если можно заклеймить поинты и начать фармит сделает это
        """
        try:
            del http_client.headers['Connection']
        except:
            pass
        try:
            del http_client.headers['Origin']   
        except:
            pass
        try:
            del http_client.headers['Content-Type']
        except:
            pass     
        http_client.headers['authority'] = 'nutsfarm.crypton.xyz'
        http_client.headers['Referer'] = 'https://nutsfarm.crypton.xyz/'
        text = f"Bearer {acces_token}"
        http_client.headers['Authorization'] = text
        response = await http_client.get(f"https://nutsfarm.crypton.xyz/api/v1/farming/current")
        response.raise_for_status()
        json_response = await response.json()
        print(json_response)
        if json_response.get('status') == 'READY_TO_CLAIM':
            await self.claim_farmed(http_client=http_client, acces_token=acces_token)
        if json_response.get('status') == 'READY_TO_FARM':
            await self.start_farm(http_client=http_client, acces_token=acces_token)
        
    async def claim_farmed(self, http_client: aiohttp.ClientSession, acces_token: str):
        http_client.headers['Referer'] = 'https://nutsfarm.crypton.xyz'
        text = f"Bearer {acces_token}"
        http_client.headers['Authorization'] = text
        claim = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/farming/claim', 
                                                    timeout=aiohttp.ClientTimeout(60))
        print(claim.status)
        del http_client.headers['Authorization']

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://ipinfo.io/ip', timeout=aiohttp.ClientTimeout(10))
            ip = (await response.text())
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def create_acc_in_bot(self, http_client: aiohttp.ClientSession):
        response = await http_client.get(f"https://nutsfarm.crypton.xyz/")
        response.raise_for_status()
        http_client.headers['Referer'] = f'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
        payload = {'authData': self.init_data}   
        payload['language'] = 'RU'
        payload['referralCode'] = 'ATADFYOPHBQFOSV'
        response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/auth/register', json=payload, 
                                                    timeout=aiohttp.ClientTimeout(60))
        response_json = await response_auth_token.json()
        self.refresh_token = response_json['refreshToken']
        self.access_token = response_json['accessToken']
        tokens = await self.claim_start_bonus(http_client=http_client)  
        return tokens    

    async def get_auth_token_static(self, http_client: aiohttp.ClientSession):
        """
            Берёт токен авторизации, который после будет использоваться для подачи запросов пользователю на сервер nuts
            - Живёт 24 часа
        """
        payload = {'refreshToken': self.refresh_token}
        response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/auth/token', json=payload, 
                                                    timeout=aiohttp.ClientTimeout(60))
        response_json = await response_auth_token.json()
        return response_json

    async def login_in_bot_1(self, http_client: aiohttp.ClientSession):
        http_client.headers['Referer'] = 'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
        http_client.headers['authority'] = 'nutsfarm.crypton.xyz'
        del http_client.headers['Connection']
        http_client.headers['Accept-Language'] = 'ru-RU,ru;q=0.9,en-US;q=0.8;q=0.7'
        http_client.headers['Content-Type'] = 'text/plain;charset=UTF-8'
        response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/auth/login', data=f'{self.init_data}', 
                                                    timeout=aiohttp.ClientTimeout(60))
        response_json = await response_auth_token.json()
        del http_client.headers['Content-Type']
        return response_json

    async def claim_start_bonus(self, http_client: aiohttp.ClientSession):
        """
                - json_auth - ACCES TOKEN для клейма старт бонуса
            После регистрации пользователя собирает start_bonus который даёт 1337 токенов, вылазит только 1 раз
            return 
            - refresh_token
            - access_token
        """
        http_client.headers['Referer'] = f'https://nutsfarm.crypton.xyz/?startapp=ref_nutsfarm_bot&tgWebAppStartParam=ref_ATADFYOPHBQFOSV'
        text = f"Bearer {self.access_token}"
        http_client.headers['Authorization'] = text
        claim = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/farming/startBonus', 
                                                    timeout=aiohttp.ClientTimeout(60))
        token_forever = await self.get_auth_token_static(http_client=http_client)
        logged_in_bot = await self.login_in_bot_1(http_client=http_client)
        http_client.headers['Accept-Language'] = 'ru-RU,ru;q=0.9,en-US;q=0.8;q=0.7'
        await self.claim_dayly_bonus(http_client=http_client, acces_token=logged_in_bot['accessToken'])
        await self.start_farm(http_client=http_client, acces_token=logged_in_bot['accessToken'])
        return {"refresh_token": self.refresh_token, "access_token": logged_in_bot['accessToken']}

    async def claim_dayly_bonus(self, http_client: aiohttp.ClientSession, acces_token: str):
        http_client.headers['Origin'] = 'https://nutsfarm.crypton.xyz'
        text = f"Bearer {acces_token}"
        http_client.headers['Authorization'] = text
        claim = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/streak/current/claim?timezone=Europe/Kiev&payForFreeze=false',    
                                                        timeout=aiohttp.ClientTimeout(60))
        #claim = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/streak/current/claim?timezone=Europe/Kiev',    
        #                                                        timeout=aiohttp.ClientTimeout(60))
        print(claim.status)

    async def start_farm(self, http_client: aiohttp.ClientSession, acces_token: str):
        text = f"Bearer {acces_token}"
        http_client.headers['Referer'] = 'https://nutsfarm.crypton.xyz/'
        http_client.headers['Origin'] = 'https://nutsfarm.crypton.xyz'
        http_client.headers['Authorization'] = text
        try:
            response_auth_token = await http_client.post('https://nutsfarm.crypton.xyz/api/v1/farming/farm', 
                                                        timeout=aiohttp.ClientTimeout(60))
            current_time = int((datetime.datetime.now()).timestamp())
            await Accounts().set_last_start_farm(session_name=self.session_name,
                                                 last_start_farm=current_time)
            self.new_start_farm_time_date = datetime.datetime.fromtimestamp(current_time)+datetime.timedelta(hours=8)
            print(response_auth_token.status)
        except:
            pass

    async def get_info_user(self, http_client: aiohttp.ClientSession, access_token: str):
        text = f"Bearer {access_token}"
        http_client.headers['Authorization'] = text
        payload = {'lang': 'EN'}
        info = await http_client.get(f"https://nutsfarm.crypton.xyz/api/v1/streak/current/info?timezone=Europe/Kiev", json=payload)
        response_json = await info.json()
        print(response_json)
        return response_json.get('balance')

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

    async def run(self, user_agent: str, proxy: str, new_bot_user: bool, session_name: str,
                    refresh_token: Union[str, None], acces_token: Union[str, None]):
        self.proxy = proxy
        s = proxy.split(":")
        proxy_connection = ProxyConnector().from_url(f"{s[0]}:{s[1]}:{s[2]}@{s[3]}:{s[4]}") if proxy else None
        headers['User-Agent'] = user_agent
        init_data = await self.get_tg_web_view(tg_client=self.tg_client, proxy=proxy)
        self.init_data = init_data
        async with aiohttp.ClientSession(headers=headers, connector=proxy_connection) as http_client:
            if new_bot_user:
                tokens = await self.create_acc_in_bot(http_client=http_client)
                accs = await Accounts().edit_account(session_name=session_name, refresh_token=tokens.get('refresh_token'),
                                                     acces_token=tokens.get('access_token'))
            else:
                #try:
                    login_in_bot = await self.login_in_bot_1(http_client=http_client)
                    self.access_token = login_in_bot['accessToken']
                    self.refresh_token = login_in_bot['refreshToken']
                    new_auth_token = await self.get_auth_token_static(http_client=http_client)
                    accs = await Accounts().edit_account(session_name=session_name, refresh_token=login_in_bot['refreshToken'],
                                        acces_token=login_in_bot['accessToken'])

                    balance = await self.get_info_user(access_token=login_in_bot['accessToken'], http_client=http_client)
                    print(f'У ЭТОГО АККАУНТА {balance} очков')
                    if new_auth_token['accessToken'] is None:
                        await self.get_info_claimed_daily_bonus(http_client=http_client, access_token=login_in_bot['accessToken'])
                        await self.get_current_farming_status(http_client=http_client,
                                        acces_token=login_in_bot['accessToken'])
                        await self.get_current_farming_status(http_client=http_client,
                                            acces_token=login_in_bot['accessToken'])
                    else:
                        await self.get_info_claimed_daily_bonus(http_client=http_client, access_token=login_in_bot['accessToken'])
                        await self.get_current_farming_status(http_client=http_client,
                                                            acces_token=login_in_bot['accessToken'])
                        await self.get_current_farming_status(http_client=http_client,
                                                            acces_token=login_in_bot['accessToken'])
                # except Exception as e:
                #     try:
                #         await self.get_info_claimed_daily_bonus(http_client=http_client, access_token=acces_token)
                #         await self.get_current_farming_status(http_client=http_client,
                #                             acces_token=acces_token)
                #         accs = await Accounts().edit_account(session_name=session_name, refresh_token=login_in_bot['refreshToken'],
                #                                     acces_token=acces_token)
                #         await self.get_current_farming_status(http_client=http_client,
                #                             acces_token=acces_token)
                #     except Exception as e:
                #         print(e)
                #         print('С ЭТИМ АККОМ ПРОБЛЕМА......')

async def run_tapper(tg_client: Client, user_agent: str, proxy: str, session_name: str, new_bot_user: bool,
                    refresh_token: Union[str, None], acces_token: Union[str, None], scheduler: AsyncIOScheduler):
    tapper = Tapper(tg_client=tg_client)
    await tapper.run(user_agent=user_agent, proxy=proxy, new_bot_user=new_bot_user,
                                          session_name=session_name, refresh_token=refresh_token,
                                          acces_token=acces_token)
    if tapper.new_start_farm_time_date is None: 
        pass
    else:
        if tapper.new_start_farm_time_date is None:
            pass
        else:
            print(tapper.new_start_farm_time_date)
            run_date=tapper.new_start_farm_time_date
            print(run_date)
            scheduler.add_job(run_tapper, 'date', run_date=run_date,
                                    kwargs={"tg_client": tg_client, 'user_agent': user_agent, 'new_bot_user': True, 
                                            'proxy': proxy, "session_name": session_name, "acces_token": acces_token, "refresh_token": refresh_token,
                                            "scheduler": scheduler})


async def a():
    accs = await Accounts().get_accounts()
    scheduler = AsyncIOScheduler()
    scheduler.start()
    for account in accs.get('unregistered_accs'):
        await asyncio.sleep(random.randint(1, 15))
        print(account.get('session_name'))
        try:
            session = await get_tg_client(session_name=account.get('session_name'), proxy=account.get('proxy'))
            async with session:
                new_start_time = await run_tapper(tg_client=session, user_agent=account.get('user_agent'), new_bot_user=True,
                                proxy=account.get('proxy'), session_name=account.get('session_name'), acces_token=None, refresh_token=None,
                                scheduler=scheduler)
        except:
            pass
    for account in accs.get('registered_accs'):
        try:
            print(account.get('session_name'))
            await asyncio.sleep(random.randint(1, 20))
            print(account.get('session_name'))
            session = await get_tg_client(session_name=account.get('session_name'), proxy=account.get('proxy'))
            async with session:
                if account.get('acces_token') is None:
                    new_start_time = await run_tapper(tg_client=session, user_agent=account.get('user_agent'), new_bot_user=False,
                                    proxy=account.get('proxy'), session_name=account.get('session_name'),
                                    acces_token=None, refresh_token=None,
                                scheduler=scheduler)
                else:
                    new_start_time = await run_tapper(tg_client=session, user_agent=account.get('user_agent'), new_bot_user=False,
                                    proxy=account.get('proxy'), session_name=account.get('session_name'),
                                    acces_token=account.get('acces_token'), refresh_token=account.get('refresh_token'),
                                scheduler=scheduler)
        except:
            pass
    await asyncio.Event().wait()

asyncio.run(a())
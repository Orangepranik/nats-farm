import json
import os, logger, asyncio

from bot.utils.file_manager import load_from_json

from typing import TypedDict, Union


class AccountsDict(TypedDict):
    registered_accs: list
    unregistered_accs: list
    parse_sessions: list


class Accounts:

    def __init__(self):
        self.workdir = 'sessions/'


    def parse_sessions(self):
        sessions = []
        for file in os.listdir(self.workdir):
            if file.endswith(".session"):
                sessions.append(file.replace(".session", ""))

        logger.logger.info(f"Searched sessions: {len(sessions)}.")
        return sessions

    async def get_accounts(self) -> AccountsDict:
        """
        Возвращает словарь с информацией об аккаунтах.

        Возвращаемое значение:
            Словарь, содержащий:
            - registered_accs: Список зарегистрированных аккаунтов (список объектов Account).
            - unregistered_accs: Список незарегистрированных аккаунтов (список объектов Account).
            - parse_sessions: Список сессий pyrogram аккаунтов (список обьектов Account)
        """
        parse_sessions = self.parse_sessions()

        print(parse_sessions)

        accounts_from_json = load_from_json('sessions/accounts.json')


        registered_accs = []
        unregistered_accs = []

        for account in accounts_from_json:
            if account.get('refresh_token', False) is False:
                unregistered_accs.append(account)
            else:
                registered_accs.append(account)
        return {"registered_accs": registered_accs, "unregistered_accs": unregistered_accs,
                "parse_sessions": parse_sessions}

    async def edit_account(self, session_name: str, refresh_token: Union[str, None], acces_token: Union[str, None]):
        """
            Перезаписывает sessions/accounts.json, где session_name соотвесует названию сессии
            Эта сессия уже будет отмечаться как зареганная в боте.
            Сначала выстраиваются зареганные незареганные в боте аккаунты, а после уже зарегестированные, зареганный аккаунт добавляют в конец
        """
        accs = await self.get_accounts()
        data = []
        for acc in accs.get('unregistered_accs'):
            if acc.get('session_name') == session_name: 
                form_data_account = {}
                form_data_account['session_name'] = session_name
                form_data_account['refresh_token'] = refresh_token
                form_data_account['acces_token'] = acces_token
                form_data_account['user_agent'] = acc.get('user_agent')
                form_data_account['proxy'] = acc.get('proxy')
                data.append(form_data_account)
            else:
                data.append(acc)
        for acc in accs.get('registered_accs'):
            data.append(acc)
        json_ = json.dumps(data, indent=4)
        with open('sessions/accounts.json', 'w') as json_file:
            json_file.write(json_)

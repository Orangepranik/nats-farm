import asyncio
import json
from datetime import datetime
import os
import random
from time import time
from typing import Any
from urllib.parse import unquote, quote, parse_qs

import aiohttp

from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw import types
from pyrogram.raw.functions.messages import RequestAppWebView

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
        self.mining_data = None
        self.user_info = None
        self.proxy = None
        self.last_event_time = None
        self.balance = 0.0
        self.template = None

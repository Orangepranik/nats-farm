from pyrogram import Client

from bot.config.config import settings

async def get_tg_client(session_name: str, proxy: str | None) -> Client:
    if not session_name:
        raise FileNotFoundError(f"Not found session {session_name}")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    proxy_dict = {
        "scheme": proxy.split(":")[0],
        "username": proxy.split(":")[1].split("//")[1],
        "password": proxy.split(":")[2],
        "hostname": proxy.split(":")[3],
        "port": int(proxy.split(":")[4])
    } if proxy else None

    tg_client = Client(
        name=session_name,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        workdir="sessions/",
        proxy=proxy_dict
    )

    return tg_client
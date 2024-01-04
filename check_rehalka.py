import asyncio

import aiohttp
import pytz
import random
import concurrent.futures


from datetime import datetime
from twocaptcha import TwoCaptcha


almaty_tz = pytz.timezone('Asia/Almaty')

TWOCAPTHCA = "twocaptcha"
REHALKA = "rehalka"

REHALKA_IP = "188.124.36.201:3005"
REHALKA_API_KEY = "74195bcd-0a3a-4b13-8711-06c6309e6840"
CAPTCHA_URL = "https://evergem.io/claim?redirect_to=/game"
CAPTCHA_KEY = "d1add268-b915-46c1-afd3-960faba20822"


async def captchaSolver(method):
    if method == TWOCAPTHCA:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            two_result = await loop.run_in_executor(pool, lambda: TwoCaptcha("5bcf672e872e4ed67e1b0a1627eece17",
                                                                         defaultTimeout=180).hcaptcha(
                sitekey='d1add268-b915-46c1-afd3-960faba20822',
                url='https://evergem.io/claim?redirect_to=/game',
            ))
            return two_result.get('code').replace(" ", "")
    elif method == REHALKA:
        async with aiohttp.ClientSession() as rh_session:
            url = f"http://{REHALKA_IP}/in.php?userkey={REHALKA_API_KEY}&host={CAPTCHA_URL}&sitekey={CAPTCHA_KEY}"
            async with rh_session.get(url) as in_response:
                in_response.raise_for_status()
                captcha_info = await in_response.text()
                if "OK" not in captcha_info:
                    raise ValueError("Getting captcha value error")
                captcha_id = captcha_info.split('|')[1]

            while True:
                await asyncio.sleep(5)

                async with aiohttp.ClientSession() as rh_res_session:
                    url = f"http://{REHALKA_IP}/res.php?userkey={REHALKA_API_KEY}&id={captcha_id}"
                    async with rh_res_session.get(url) as res_response:
                        res_response.raise_for_status()
                        response_text = await res_response.text()

                    if response_text in ["ERROR_KEY_DOES_NOT_EXIST", "ERROR_ZERO_BALANCE", "ERROR_NO_SLOT_AVAILABLE",
                                  "ERROR_CAPTCHA_UNSOLVABLE", "ERROR_WRONG_SAITKEY", "ERROR_WRONG_CAPTCHA_ID"]:
                        raise ValueError(f"Getting result: {response_text}")
                    elif response_text == "CAPCHA_NOT_READY":
                        continue
                    elif response_text.startswith("OK"):
                        return response_text.split("|")[1]

    return None


async def check():
    current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time}: {1} начинаю решать капчу")
    gh = await captchaSolver(REHALKA)

    current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time}: {1} решил капчу")
    print(gh)


asyncio.run(check())

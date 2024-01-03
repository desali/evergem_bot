import asyncio
import pytz
import aiohttp
import random

from datetime import datetime
from openpyxl import load_workbook
from twocaptcha import TwoCaptcha

number_of_accounts = 1

almaty_tz = pytz.timezone('Asia/Almaty')

workbook = load_workbook(filename='info.xlsx')
sheet = workbook.active
data = []

min_row = 2
max_row = min_row + number_of_accounts - 1
for row in sheet.iter_rows(min_row=min_row, max_row=max_row, values_only=True):
    data.append({
        'name': row[0],
        'proxy': row[1],
        'ua': row[2],
        'item_id': row[7],
        'token': row[8],
        'cookie': row[9],
        'sleep_min': row[10],
        'sleep_max': row[11]
    })


async def work(account, session):
    claim_count = 1

    name = account['name']
    proxy = account['proxy']
    user_agent = account['ua']
    item_id = account['item_id']
    token = account['token']
    cookie = account['cookie']
    sleep_min = int(account['sleep_min'])
    sleep_max = int(account['sleep_max'])

    while True:
        try:
            request_kwargs = {"timeout": 10}
            if proxy.lower() != 'no':
                proxy_creds = proxy.split(':')
                request_kwargs["proxy"] = f"http://{proxy_creds[2]}:{proxy_creds[3]}@{proxy_creds[0]}:{proxy_creds[1]}"
            async with session.get("http://httpbin.org/ip", **request_kwargs) as response:
                response.raise_for_status()
        except Exception as e:
            current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{current_time}: {name}: {proxy}: Ошибка в проверке прокси: {e}")
        else:
            try:
                solver = TwoCaptcha("5bcf672e872e4ed67e1b0a1627eece17")

                result = solver.hcaptcha(
                    sitekey='d1add268-b915-46c1-afd3-960faba20822',
                    url='https://evergem.io/claim?redirect_to=/game',
                )
                gh = result.get('code')
                gh = gh.replace(" ", "")
            except Exception as e:
                current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                print(f"{current_time}: {name}: Ошибка в решении капчи: {e}")
            else:
                try:
                    url = 'https://evergem.io/claim'
                    params = {
                        'redirect_to': '/game'
                    }
                    payload = {
                        'item_id': f'{item_id}',
                        'h-captcha-response': gh,
                        'castle_request_token': token
                    }
                    headers = {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'uk,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6,bg;q=0.5,es;q=0.4',
                        'Cache-Control': 'max-age=0',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Cookie': f'{cookie}',
                        'Origin': 'null',
                        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                        'Sec-Ch-Ua-Mobile': '?0',
                        'Sec-Ch-Ua-Platform': '"Windows"',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'same-origin',
                        'Sec-Fetch-User': '?1',
                        'Upgrade-Insecure-Requests': '1',
                        'User-Agent': f'{user_agent}'
                    }

                    request_kwargs = {}
                    if proxy.lower() != 'no':
                        proxy_creds = proxy.split(':')
                        request_kwargs["proxy"] = f"http://{proxy_creds[2]}:{proxy_creds[3]}@{proxy_creds[0]}:{proxy_creds[1]}"
                    async with session.post(url,
                                            headers=headers,
                                            params=params,
                                            data=payload,
                                            **request_kwargs) as response:
                        response.raise_for_status()
                except Exception as e:
                    current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{current_time}: {name}: Ошибка во время клейма: {e}")
                else:
                    current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{current_time}: {name}: Удачный клейм: {claim_count}")
                    claim_count += 1

        await asyncio.sleep(random.randint(sleep_min, sleep_max))


async def main():
    async with aiohttp.ClientSession() as session:
        tasks = []

        for account in data:
            task = asyncio.create_task(work(account, session))
            tasks.append(task)

        await asyncio.gather(*tasks)


asyncio.run(main())

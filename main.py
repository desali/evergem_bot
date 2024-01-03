import asyncio
import pytz
import aiohttp
import random
import concurrent.futures


from datetime import datetime
from openpyxl import load_workbook
from twocaptcha import TwoCaptcha

from bs4 import BeautifulSoup

number_of_accounts = 45

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


async def captchaSolver():
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, lambda: TwoCaptcha("5bcf672e872e4ed67e1b0a1627eece17",
                                                                     defaultTimeout=180).hcaptcha(
            sitekey='d1add268-b915-46c1-afd3-960faba20822',
            url='https://evergem.io/claim?redirect_to=/game',
        ))
        return result


async def work(account):
    async with aiohttp.ClientSession() as session:

        claim_count = 1

        name = account['name']
        proxy = account['proxy']
        user_agent = account['ua']
        item_id = account['item_id']
        token = account['token']
        cookie = account['cookie']
        sleep_min = int(account['sleep_min'])
        sleep_max = int(account['sleep_max'])
        # print(f"{name} данные загружены")

        while True:
            try:
                # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                # print(f"{current_time}: {name} начинаю решать капчу")
                result = await captchaSolver()

                gh = result.get('code')
                gh = gh.replace(" ", "")
                # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                # print(f"{current_time}: {name} решил капчу")
                # print(gh)
            except Exception as e:
                current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                print(f"{current_time}: {name}: Ошибка в решении капчи: {e}")
            else:
                try:
                    # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                    # print(f"{current_time}: {name} начинаю клейм")
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

                    proxy_url = None
                    if proxy.lower() != 'no':
                        proxy_creds = proxy.split(':')
                        proxy_url = f"http://{proxy_creds[2]}:{proxy_creds[3]}@{proxy_creds[0]}:{proxy_creds[1]}"
                    # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                    # print(f"{current_time}: {name} перед запросом")
                    if proxy_url:
                        async with session.post(url,
                                                headers=headers,
                                                params=params,
                                                data=payload,
                                                proxy=proxy_url) as response:
                            # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                            # print(f"{current_time}: {name} внутри запроса с прокси")
                            response.raise_for_status()
                            text = await response.text()
                    else:
                        async with session.post(url,
                                                headers=headers,
                                                params=params,
                                                data=payload) as response:
                            # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                            # print(f"{current_time}: {name} внутри запроса без прокси")
                            response.raise_for_status()
                            text = await response.text()
                except Exception as e:
                    current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{current_time}: {name}: Ошибка во время клейма: {e}")
                else:
                    soup = BeautifulSoup(text, 'html.parser')
                    balance_info_container = soup.find('div', class_='balance-info')
                    top_wrap_container = soup.find('div', class_='top-wrap')

                    balance_info_p_tags = balance_info_container.find_all('p')
                    balance_hpe = next((tag.text.strip() for tag in balance_info_p_tags if "HPE" in tag.text), None)
                    balance_usd = next((tag.text.strip() for tag in balance_info_p_tags if "$" in tag.text), None)

                    rate_wrap_container = top_wrap_container.find('div', class_='rate-wrap')
                    rate_hpe_day = next((tag.text.strip() for tag in rate_wrap_container.find_all('span') if "HPE/day" in tag.text),None)

                    current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{current_time}: {name}: Удачный клейм: {claim_count}, Баланс: {balance_hpe} ({balance_usd}) | {rate_hpe_day}")
                    claim_count += 1

                    balance_hpe_float = float(balance_hpe.split(' ')[0])
                    rate_hpe_float_day = float(rate_hpe_day.split(' ')[0])

                    if balance_hpe_float >= rate_hpe_float_day/4:
                        # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                        # print(f"{current_time}: {name}: Вывожу HPE: {balance_hpe_float}")

                        try:
                            url = 'https://evergem.io/withdraw'
                            params = {
                                'redirect_to': '/game'
                            }
                            payload = {
                                'amount': balance_hpe_float
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

                            proxy_url = None
                            if proxy.lower() != 'no':
                                proxy_creds = proxy.split(':')
                                proxy_url = f"http://{proxy_creds[2]}:{proxy_creds[3]}@{proxy_creds[0]}:{proxy_creds[1]}"
                            # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                            # print(f"{current_time}: {name} перед запросом")
                            async with aiohttp.ClientSession() as withdraw_session:
                                if proxy_url:
                                    async with withdraw_session.post(url,
                                                            headers=headers,
                                                            params=params,
                                                            data=payload,
                                                            proxy=proxy_url) as response:
                                        # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                                        # print(f"{current_time}: {name} внутри запроса с прокси")
                                        response.raise_for_status()
                                else:
                                    async with withdraw_session.post(url,
                                                            headers=headers,
                                                            params=params,
                                                            data=payload) as response:
                                        # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                                        # print(f"{current_time}: {name} внутри запроса без прокси")
                                        response.raise_for_status()
                        except Exception as e:
                            current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                            print(f"{current_time}: {name}: Ошибка во время вывода токенов: {e}")
                        else:
                            current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
                            print(f"{current_time}: {name}: Удачный вывод: {balance_hpe_float} HPE")

            # current_time = datetime.now(almaty_tz).strftime("%Y-%m-%d %H:%M:%S")
            # print(f"{current_time}: {name} засыпает")
            await asyncio.sleep(random.randint(sleep_min, sleep_max))


async def main():
    tasks = []

    for account in data:
        task = asyncio.create_task(work(account))
        tasks.append(task)

    await asyncio.gather(*tasks)


asyncio.run(main())

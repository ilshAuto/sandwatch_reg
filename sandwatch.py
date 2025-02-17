import asyncio
import sys
import random
import string
from typing import Optional

import cloudscraper

import json

import httpx
from loguru import logger

logger.remove()
logger.add(sys.stdout, format='<g>{time:YYYY-MM-DD HH:mm:ss:SSS}</g> | <c>{level}</c> | <level>{message}</level>')
"""
 !!!!!!!!    填写你的inviteCode   !!!!!!!
"""

invite_code = ['849BBF', '7DD906', 'AF0649']


class ScraperReq:
    def __init__(self, proxy: dict, header: dict):
        self.scraper = cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False,
        })
        self.proxy: dict = proxy
        self.header: dict = header
        self.sol_address:Optional[str] = None

    def post_req(self, url, req_json, req_param):
        # logger.info(self.header)
        # logger.info(req_json)
        return self.scraper.post(url=url, headers=self.header, json=req_json, proxies=self.proxy, params=req_param)

    async def post_async(self, url, req_param=None, req_json=None):
        return await asyncio.to_thread(self.post_req, url, req_json, req_param)

    def get_req(self, url, req_param):
        return self.scraper.get(url=url, headers=self.header, params=req_param, proxies=self.proxy)

    async def get_async(self, url, req_param=None, req_json=None):
        return await asyncio.to_thread(self.get_req, url, req_param)


class SandWatch:

    def __init__(self, index: int, proxy: str, headers: dict, mnemonic: str, invite: str, JS_SERVER: str):
        proxies = {
            'http': proxy,
            'https': proxy,
        }
        self.index: Optional[int] = index
        self.proxy = proxy
        self.scrape: Optional[ScraperReq] = ScraperReq(proxies, headers)
        self.sol_address:Optional[str] = None
        # self.signed_message:Optional[str] = None
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.mnemonic = mnemonic
        self.invite = invite
        self.JS_SERVER = JS_SERVER

    async def login(self):
        sign_payload = {
            "mnemonic": self.mnemonic,
            "payload": "Log in to Sandwatch",
            "proxy": self.proxy
        }
        res = None
        for i in range(3):
            try:
                res = await httpx.AsyncClient().post(f'http://{self.JS_SERVER}:3666/api/solana/sign', json=sign_payload,
                                                     timeout=30)
                break
            except Exception as e:
                if i == 2:
                    logger.info(f'请求签名失败')
                    return
                logger.info(f'请求签名异常，睡眠10s，{e}')
                await asyncio.sleep(10)
                continue
        self.sol_address = res.json()['address']
        logger.info(f'{self.index}, {self.proxy}: sol签名结果：{res.text}')

        url = "https://tyrgts2xzb.execute-api.us-east-1.amazonaws.com/v1/auth/access_token"
        payload = {
            "publicKey": self.sol_address,
            "signedMessage": res.json()['signature']
        }
        response = await self.scrape.post_async(url, req_json=payload)
        logger.info(f'{self.index}, {self.proxy}: 登录响应：{response.text}')

        # 解析嵌套的JSON响应
        outer_result = response.json()
        inner_result = json.loads(outer_result['body'])

        self.token = inner_result['token']
        self.refresh_token = inner_result['refresh_token']
        logger.info(f'{self.index}, {self.proxy}: token：{self.token}')
        self.scrape.header.update({'authorization': f'Bearer {self.token}'})
        return True

    async def user(self):
        url = f'https://tyrgts2xzb.execute-api.us-east-1.amazonaws.com/v1/user/{self.sol_address}'
        res = await self.scrape.get_async(url)
        logger.info(f'{self.index}, {self.proxy}: user-info:{res.text}')

        response_data = res.json()
        if "profile" in response_data:
            print(response_data)
            # 用户已存在，显示用户信息
            profile = response_data["profile"]
            seat = response_data["seat"]
            logger.info(f'{self.index}, {self.proxy}: 当前用户信息：'
                      f'用户名: {profile["username"]}, '
                      f'座位: {seat["seat_row"]}-{seat["seat_number"]}, '
                      f'抽奖号: {profile["lottery_ticket"]}')
        elif 'User not found' in res.text:

            logger.debug(f'{self.index}, {self.proxy}: 没有注册，开始注册！')
            # 获取座位信息
            get_seat_url = f'https://tyrgts2xzb.execute-api.us-east-1.amazonaws.com/v1/seat/seat-for-invite-code/{self.invite}'
            seat_res = await self.scrape.get_async(get_seat_url)
            outer_result = seat_res.json()
            inner_body = json.loads(outer_result['body'])
            seat_info = inner_body['seat']

            # 尝试创建用户，最多3次
            retry_count = 0
            while retry_count < 3:
                # 生成随机用户名 (8-12个字符)
                username_length = random.randint(8, 12)
                username = ''.join(random.choices(string.ascii_lowercase, k=username_length))

                # 开始创建seat
                create_seat_url = 'https://tyrgts2xzb.execute-api.us-east-1.amazonaws.com/v1/user/create-profile-assign-seat'
                create_seat_payload = {
                    "username": username,
                    "user_id": self.sol_address,
                    "invite_code": self.invite,
                    "seat_row": seat_info['seat_row'],
                    "seat_number": seat_info['seat_number'],
                    "lottery_ticket": seat_info['seat_lottery_number']
                }
                res = await self.scrape.post_async(create_seat_url, req_json=create_seat_payload)
                response_text = res.text

                if "Username already taken" in response_text:
                    retry_count += 1
                    logger.warning(f'{self.index}, {self.proxy}: 用户名已存在，第{retry_count}次重试')
                    continue

                # 解析成功响应
                response_data = res.json()
                if "profile" in response_data:
                    profile = response_data["profile"]
                    seat = response_data["seat"]
                    logger.info(f'{self.index}, {self.proxy}: 创建成功！ '
                              f'用户名: {profile["username"]}, '
                              f'用户ID: {profile["user_id"]}, '
                              f'座位: {seat["row"]}-{seat["number"]}, '
                              f'抽奖号: {profile["lottery_ticket"]}')
                    break
                else:
                    retry_count += 1
                    logger.error(f'{self.index}, {self.proxy}: 创建失败，响应异常：{response_text}')

            if retry_count >= 3:
                logger.error(f'{self.index}, {self.proxy}: 创建用户重试3次都失败了')

    async def popcorn(self):
        url = f'https://tyrgts2xzb.execute-api.us-east-1.amazonaws.com/v1/popcorn/popcorn'
        params = {'user_id': self.sol_address}
        res = await self.scrape.get_async(url, req_param=params)

        response_data = res.json()
        if response_data['statusCode'] == 200:
            popcorn_info = response_data['body']
            logger.info(f'{self.index}, {self.proxy}: 爆米花信息：'
                      f'总数量: {popcorn_info["total_popcorn"]}, '
                      f'当前倍数: {popcorn_info["current_multiplier"]}x')

    async def start_watch(self):
        await self.login()
        await self.user()
        await self.popcorn()

async def run(acc: dict, index:int, JS_SERVER:str):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://www.sandwatch.com',
        'referer': 'https://www.sandwatch.com/'
    }
    proxy = acc.get('proxy')
    mnemonic = acc.get('mnemonic')
    invite = acc.get('invite')
    # index = 0
    sand = SandWatch(index, proxy, headers, mnemonic, invite, JS_SERVER)
    try:
        await sand.start_watch()
    except Exception as e:
        logger.error(f'{index}, {proxy}, error: {e}')

async def main(JS_SERVER:str):
    accs = []
    with open('./acc', 'r', encoding='utf-8') as file:
        for line in file.readlines():
            phrase, proxy = line.strip().split('----')
            invite = random.choice(invite_code)
            accs.append({'mnemonic': phrase, 'proxy': proxy, 'invite': invite})
    tasks = []
    for index, acc in enumerate(accs):
        tasks.append(run(acc, index, JS_SERVER))

    await asyncio.gather(*tasks)




if __name__ == '__main__':
    logger.info('🚀 [ILSH] SANDWATCH v1.0 | Airdrop Campaign Live')
    logger.info('🌐 ILSH Community: t.me/ilsh_auto')
    logger.info('🐦 X(Twitter): https://x.com/hashlmBrian')
    logger.info('☕ Pay meCoffe：USDT（TRC20）:TAiGnbo2isJYvPmNuJ4t5kAyvZPvAmBLch')

    JS_SERVER = '127.0.0.1'

    print('----' * 30)
    print('请验证, JS_SERVER的host是否正确')
    print('pay attention to whether the host of the js service is correct')
    print('----' * 30)
    asyncio.run(main(JS_SERVER))

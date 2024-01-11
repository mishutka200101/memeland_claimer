import asyncio

import aiohttp
from aiohttp_proxy import ProxyConnector
from eth_account import Account
from eth_account.account import LocalAccount
from eth_account.messages import encode_defunct
from loguru import logger
from pyuseragents import random as random_useragent

from utils import loader, format_private_key
from utils.misc import solve_recaptcha, solve_hcaptcha


class TaskCompleter:
    def __init__(self,
                 private_key: str):
        self.private_key: str = private_key
        self.account: LocalAccount = Account.from_key(private_key=private_key)

    def sign_message(self,
                     sign_text: str) -> str:
        return Account.sign_message(signable_message=encode_defunct(
            text=sign_text),
            private_key=self.account.key).signature.hex()

    async def do_login(self,
                       client: aiohttp.ClientSession) -> str | None:
        r: None = None
        sign_text: str = 'The wallet will be used for MEME allocation. If you referred friends, family, lovers or ' \
                         'strangers, ensure this wallet has the NFT you referred.\n\nBut also...\n\nNever gonna give ' \
                         'you up\n\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make ' \
                         'you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\n\nWallet: ' + \
                         self.account.address[:5] + "..." + self.account.address[-4:]

        while True:
            try:
                signed_message: str = self.sign_message(sign_text=sign_text)

                r: aiohttp.ClientResponse = await client.post(url='https://memefarm-api.memecoin.org/user/wallet-auth',
                                                              json={
                                                                  'address': self.account.address,
                                                                  'delegate': self.account.address,
                                                                  'message': sign_text,
                                                                  'signature': signed_message
                                                              })

                if (await r.json()).get('error', '') == 'unauthorized':
                    logger.error(f'{self.private_key} | Not Registered')
                    return None

                return (await r.json(content_type=None))['accessToken']

            except Exception as error:
                if r:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при авторизации: {error}, ответ: '
                                 f'{await r.text()}')

                else:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при авторизации: {error}')

    # async def get_verify_status(self,
    #                             client: aiohttp.ClientSession) -> bool:
    #     r: None = None
    #
    #     while True:
    #         try:
    #             r: aiohttp.ClientResponse = await client.get(url='https://memefarm-api.memecoin.org/user/info',
    #                                                          json=False)
    #
    #             return (await r.json(content_type=None))['verification']
    #
    #         except Exception as error:
    #             if r:
    #                 logger.error(f'{self.private_key} | Неизвестная ошибка при получении статуса верификации: {error}, '
    #                              f'ответ: {await r.text()}')
    #
    #             else:
    #                 logger.error(f'{self.private_key} | Неизвестная ошибка при получении статуса верификации: {error}')

    async def verify_completion(self,
                                client: aiohttp.ClientSession) -> bool:
        r: None = None

        while True:
            try:
                r: aiohttp.ClientResponse = await client.post(
                    url='https://memefarm-api.memecoin.org/user/verify/wallet-balance',
                    json=False)

                return (await r.json(content_type=None))['status'] == 'success'

            except Exception as error:
                if r:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при подтверждении выполнения: {error}, '
                                 f'ответ: {await r.text()}')

                else:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при подтверждении выполнения: {error}')

    async def recaptcha_solver(self,
                               client: aiohttp.ClientSession) -> None:
        r: None = None

        while True:
            try:
                recaptcha_token: str = await solve_recaptcha(private_key=self.private_key)

                r: aiohttp.ClientResponse = await client.post(
                    url='https://memefarm-api.memecoin.org/user/verify/recaptcha',
                    json={
                        'code': recaptcha_token
                    })

                if (await r.json(content_type=None))['status'] == 'success':
                    logger.success(f'{self.private_key} | Успешно решил reCaptcha')
                    return

                logger.error(f'{self.private_key} | Ошибка при отправки решения reCaptcha, ответ: {await r.text()}')

            except Exception as error:
                if r:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при решении Google reCaptcha: {error}, '
                                 f'ответ: {await r.text()}')

                else:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при решении Google reCaptcha: {error}')

    async def hcaptcha_solver(self,
                              client: aiohttp.ClientSession) -> None:
        r: None = None

        while True:
            try:
                captcha_response, user_agent = await solve_hcaptcha(private_key=self.private_key)
                client.headers['user-agent']: str = user_agent

                r: aiohttp.ClientResponse = await client.post(
                    url='https://memefarm-api.memecoin.org/user/verify/hcaptcha',
                    json={
                        'code': captcha_response
                    })

                if (await r.json(content_type=None))['status'] == 'success':
                    logger.success(f'{self.private_key} | Успешно решил hCaptcha')
                    return

                logger.error(f'{self.private_key} | Ошибка при отправки решения hCaptcha, ответ: {await r.text()}')

            except Exception as error:
                if r:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при решении Google reCaptcha: {error}, '
                                 f'ответ: {await r.text()}')

                else:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при решении Google reCaptcha: {error}')

    async def task_completer(self,
                             account_data: str,
                             proxy: str | None = None):
        async with aiohttp.ClientSession(connector=ProxyConnector.from_url(url=proxy,
                                                                           ssl=False,
                                                                           verify_ssl=None,
                                                                           ttl_dns_cache=300) if proxy \
                else aiohttp.TCPConnector(
            ssl=False,
            verify_ssl=None,
            ttl_dns_cache=300
        ),
                                         headers={
                                             'accept': 'application/json',
                                             'accept-language': 'ru,en;q=0.9',
                                             'content-type': 'application/json',
                                             'origin': 'https://www.memecoin.org',
                                             'user-agent': random_useragent()
                                         }) as client:
            auth_token: str | None = await self.do_login(client=client)

            if not auth_token:
                return

            client.headers['Authorization']: str = f'Bearer {auth_token}'

            tasks: list = [
                asyncio.create_task(coro=self.recaptcha_solver(client=client)),
                asyncio.create_task(coro=self.hcaptcha_solver(client=client))
            ]

            await asyncio.gather(*tasks)

            await self.verify_completion(client=client)


async def task_completer(account_data: str,
                         proxy: str | None = None) -> None:
    async with loader.semaphore:
        private_key: str | None = format_private_key(text=account_data)

        if not private_key:
            logger.error(f'{account_data} | Не удалось найти Private-Key в строке')
            return

        await TaskCompleter(private_key=private_key).task_completer(proxy=proxy,
                                                                    account_data=account_data)

import aiofiles
import aiohttp
from aiohttp_proxy import ProxyConnector
from eth_account import Account
from eth_account.account import LocalAccount
from eth_account.messages import encode_defunct
from loguru import logger
from pyuseragents import random as random_useragent

from utils import loader, format_private_key


class BalanceParser:
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
                         'you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make ' \
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

    async def get_balance(self,
                          client: aiohttp.ClientSession) -> tuple[int, int]:
        r: None = None

        while True:
            try:
                r: aiohttp.ClientResponse = await client.get(url='https://memefarm-api.memecoin.org/user/tasks',
                                                             json=False)

                return ((await r.json(content_type=None))['points']['current'],
                        (await r.json(content_type=None))['points']['referral'])

            except Exception as error:
                if r:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при получении баланса: {error}, ответ: '
                                 f'{await r.text()}')

                else:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при получении баланса: {error}')

    async def balance_parser(self,
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
            account_balance, refs_count = await self.get_balance(client=client)

        logger.success(f'{account_data} | {account_balance} MEME | {refs_count} REFS')

        async with loader.lock:
            async with aiofiles.open(file='result/parsed_balance.txt',
                                     mode='a',
                                     encoding='utf-8-sig') as file:
                await file.write(f'{account_data} | {account_balance} MEME | {refs_count} REFS\n')


async def balance_parser(account_data: str,
                         proxy: str | None = None) -> None:
    async with loader.semaphore:
        private_key: str | None = format_private_key(text=account_data)

        if not private_key:
            logger.error(f'{account_data} | Не удалось найти Private-Key в строке')
            return

        await BalanceParser(private_key=private_key).balance_parser(proxy=proxy,
                                                                    account_data=account_data)

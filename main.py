import asyncio
from itertools import cycle
from os import mkdir
from os.path import exists
from sys import stderr

from better_proxy import Proxy
from loguru import logger

from core import balance_parser, task_completer
from utils import loader

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' | <level>{level: <8}</level>'
                          ' | <cyan>{line}</cyan>'
                          ' - <white>{message}</white>')


async def main() -> None:
    match user_action:
        case 1:
            tasks: list = [
                asyncio.create_task(coro=balance_parser(account_data=current_account,
                                                        proxy=next(proxies_cycled) if proxies_cycled else None))
                for current_account in accounts_list
            ]

            await asyncio.gather(*tasks)

        case 2:
            tasks: list = [
                asyncio.create_task(coro=task_completer(account_data=current_account,
                                                        proxy=next(proxies_cycled) if proxies_cycled else None))
                for current_account in accounts_list
            ]

            await asyncio.gather(*tasks)


if __name__ == '__main__':
    if not exists(path='result'):
        mkdir(path='result')

    with open(file=f'data/accounts.txt',
              mode='r',
              encoding='utf-8-sig') as file:
        accounts_list: list[str] = [row.strip() for row in file]

    with open(file=f'data/proxies.txt',
              mode='r',
              encoding='utf-8-sig') as file:
        proxies_list: list[str] = [Proxy.from_str(proxy=row.strip()).as_url for row in file]

    logger.success(f'Успешно загружено {len(accounts_list)} ACCOUNTS / {len(proxies_list)} PROXY')

    user_action: int = int(input('\n1. Спарсить баланс'
                                 '\n2. Подтвердить выполнение последнего задания'
                                 '\nВыберите действие: '))
    threads: int = int(input('Threads: '))
    print()
    loader.semaphore = asyncio.Semaphore(value=threads)

    if proxies_list:
        proxies_cycled: cycle = cycle(proxies_list)

    else:
        proxies_cycled: None = None

    try:
        import uvloop

        uvloop.run(main())

    except ModuleNotFoundError:
        asyncio.run(main())

    logger.success('Работа успешно завершена')
    input('\nPress Enter to Exit..')

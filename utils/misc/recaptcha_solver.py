import aiohttp
from loguru import logger

from data import config, constants


class ReCaptchaSolver:
    def __init__(self,
                 private_key: str) -> None:
        self.private_key: str = private_key

    async def create_task(self) -> int:
        r: None = None

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    r: aiohttp.ClientResponse = await session.post(url='https://api.capmonster.cloud/createTask',
                                                                   json={
                                                                       'clientKey': config.CAPMONSTER_API_KEY,
                                                                       'task': {
                                                                           'type': 'RecaptchaV2Task',
                                                                           'websiteURL': constants.WEBSITE_URL,
                                                                           'websiteKey': constants.RECAPTCHA_KEY
                                                                       }
                                                                   })
                    return (await r.json(content_type=None))['taskId']

            except Exception as error:
                if r:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при создании задачи на решение reCaptcha: '
                                 f'{error}, ответ: {await r.text()}')

                else:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при создании задачи на решение reCaptcha: '
                                 f'{error}')

    async def get_task_result(self,
                              task_id: int | str) -> str | None:
        r: None = None

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    r: aiohttp.ClientResponse = await session.post(url='https://api.capmonster.cloud/getTaskResult',
                                                                   json={
                                                                       'clientKey': config.CAPMONSTER_API_KEY,
                                                                       'taskId': task_id
                                                                   })

                    if (await r.json(content_type=None))['errorId'] != 0:
                        logger.error(f'{self.private_key} | Ошибка при получении результата ответа, ответ: '
                                     f'{await r.text()}')
                        return

                    if (await r.json(content_type=None)).get('solution'):
                        return (await r.json(content_type=None))['solution']['gRecaptchaResponse']

            except Exception as error:
                if r:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при получении решения reCaptcha: {error}, '
                                 f'ответ: {await r.text()}')

                else:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при получении решения reCaptcha: {error}')

    async def recaptcha_solver(self) -> str:
        while True:
            task_id: int = await self.create_task()
            captcha_result: str | None = await self.get_task_result(task_id=task_id)

            if captcha_result:
                return captcha_result


async def solve_recaptcha(private_key: str) -> str:
    logger.info(f'{private_key} | Начинаю решение reCaptcha')

    return await ReCaptchaSolver(private_key=private_key).recaptcha_solver()

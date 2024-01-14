from data import config
from loguru import logger
import aiohttp


async def change_proxy_by_url(private_key: str) -> None:
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(
                        ssl=False,
                        verify_ssl=None,
                        ttl_dns_cache=300
                )) as client:
        r: aiohttp.ClientResponse = await client.get(url=config.CHANGE_PROXY_URL)

        logger.info(f'{private_key} | Changed Proxy by URL status: {r.status}')

from bs4 import BeautifulSoup
from contextlib import asynccontextmanager
from fake_useragent import UserAgent
from httpx import AsyncClient, RequestError, ReadTimeout, Response as httpx_Response, ConnectTimeout
from DrissionPage import ChromiumPage
from typing import AsyncGenerator, Iterable, TypeVar

from constants import DNS_SHOP, COOKIES_ARE, PRODUCTS_LINKS

import asyncio
import time


T = TypeVar('T', list[str], list[dict[str, str]])


class ParserDnsShop:

    def __init__(self) -> None:
        self.ua = UserAgent().chrome
        self.cookie: dict[str, str] = {COOKIES_ARE: ""}
        self.max_request = 24
        self.time_sleep_selenium = 2
        self.__auto_update_trigger = False
        self.__update_cookies_task = None
        self.__lock = asyncio.Lock()

    async def while_update_cookies(self) -> None:
        loop = asyncio.get_running_loop()

        while self.__auto_update_trigger:
            async with self.__lock:
                while not self.cookie[COOKIES_ARE]:
                    self.cookie[COOKIES_ARE] = await loop.run_in_executor(None, self.get_cookies) or ""

            await asyncio.sleep(10*60)
            self.cookie[COOKIES_ARE] = ""

    @asynccontextmanager
    async def auto_update_cookies(self) -> AsyncGenerator[None, None]:
        self.__auto_update_trigger = True

        try:
            self.__update_cookies_task = asyncio.create_task(self.while_update_cookies())
            await asyncio.sleep(10)
            yield
        finally:
            assert self.__update_cookies_task is not None

            self.__auto_update_trigger = False
            self.__update_cookies_task.cancel()

    def get_cookies(self) -> str:
        try:
            cookie = ""
            page = ChromiumPage()
            page.get(DNS_SHOP, timeout=3)
            time.sleep(self.time_sleep_selenium)

            cookies = page.cookies()
            cookie = "; ".join((f"{item['name']}={item['value']}" for item in cookies))

            page.quit()

            return cookie

        except Exception:
            return ""

    async def _create_request(
        self, urls: Iterable[str], cookie: dict[str, str]
    ) -> tuple[httpx_Response, ...]:
        result = []

        async with self.__lock:
            async with AsyncClient() as client:
                try:
                    async with asyncio.TaskGroup() as tg:

                        for url in urls:
                            result.append(
                                tg.create_task(
                                    client.get(
                                        url=url,
                                        cookies=cookie,
                                    )
                                )
                            )
                except (RequestError, ReadTimeout, ConnectTimeout) as err:
                    raise Exception(f"Произошла ошибка - {err}")

            return tuple(response for i in result if (response := i.result()) and response.status_code == 200)

    def _parse_xml(self, data: tuple[str, ...]) -> list[str]:
        links = []

        for item in data:
            soup = BeautifulSoup(item, "xml")

            for link in soup.findAll("loc"):
                links.append(link.getText("", True))

        return links

    def _parse_guid(self, data: tuple[httpx_Response, ...]) -> list[dict[str, str]]:
        result = []

        for item in data:
            soup = BeautifulSoup(item.text, "lxml")
            block = soup.find("div", {"class": "container product-card"})

            if block:
                result.append(
                    {"url": str(item.request.url), "guid": block["data-product-card"]}  # type: ignore
                )

        return result

    async def get_all_links_product(self) -> list[str]:
        response = await self._create_request(PRODUCTS_LINKS, cookie=self.cookie)
        links = self._parse_xml(data=tuple(i.text for i in response))

        return links

    async def __get_batch_request_and_reload_cookie(
        self, data: T
    ) -> AsyncGenerator[T, None]:

        for start in range(0, len(data), self.max_request):
            yield data[start:start + self.max_request]

    async def get_all_guid_product(self, data: list[str]) -> list[dict[str, str]]:
        result = []

        async for batch in self.__get_batch_request_and_reload_cookie(data=data):

            response = await self._create_request(urls=batch, cookie=self.cookie)

            result.extend(self._parse_guid(data=response))

        return result

    async def get_all_info_product(
        self, data: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        response_data = {}

        async for batch in self.__get_batch_request_and_reload_cookie(data=data):
            urls = []

            for item in batch:
                urls.append(
                    f"https://www.dns-shop.ru/product/microdata/{item['guid']}/"
                )

            response = await self._create_request(urls=urls, cookie=self.cookie)

            for item in response:
                if (data_resp := item.json()) and data_resp.get("result"):
                    response_data[
                        data_resp["data"]
                        .get("offers", {})
                        .get("url", str(item.request.url))
                    ] = {
                        "sku": data_resp["data"]["sku"],
                        "brand": data_resp["data"].get("brand", {}).get("name", ""),
                        "images": data_resp["data"].get("image", []),
                        "price": data_resp["data"].get("offers", {}).get("price", ""),
                        "name": data_resp["data"]["name"],
                        "description": data_resp["data"]["description"],
                    }

            await asyncio.sleep(0.4)

        for item in data:
            if resp_data := response_data.get(item["url"]):
                item.update(resp_data)

        return data

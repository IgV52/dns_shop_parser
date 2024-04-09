from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from fake_useragent import UserAgent
from httpx import AsyncClient, RequestError, ReadTimeout, Response as httpx_Response, ConnectTimeout
from seleniumwire.webdriver import Chrome, ChromeOptions
from seleniumwire.request import Request as sw_Request
from typing import AsyncGenerator, Iterable, TypeVar

from constants import DNS_SHOP, COOKIES_ARE, PRODUCTS_LINKS

import asyncio


T = TypeVar('T', list[str], list[dict[str, str]])


class ParserDnsShop:

    def __init__(self) -> None:
        self.ua = UserAgent()
        self.cookie: dict[str, str] = {COOKIES_ARE: ""}
        self.max_request = 24
        self.time_sleep_selenium = 2
        self.__auto_update_trigger = False
        self.__time_sleep_done = True
        self.__update_cookies_task = None

    def _run_driver(
        self, options: dict[str, ChromeOptions | dict[str, str | int]]
    ) -> Chrome:
        return Chrome(**options)

    async def while_update_cookies(self) -> None:
        while self.__auto_update_trigger:
            if not self.cookie[COOKIES_ARE] or self.__time_sleep_done:
                await self._driver_run(url=DNS_SHOP)
            else:
                await asyncio.sleep(11*60)
                self.__time_sleep_done = True

    @asynccontextmanager
    async def auto_update_cookies(self) -> AsyncGenerator[None, None]:
        try:
            while not self.cookie[COOKIES_ARE]:
                await self._driver_run(url=DNS_SHOP)

            self.__auto_update_trigger = True
            self.__update_cookies_task = asyncio.create_task(self.while_update_cookies())
            yield
        finally:
            assert self.__update_cookies_task is not None

            self.__auto_update_trigger = False
            self.__update_cookies_task.cancel()

    @asynccontextmanager
    async def get_driver(
        self, loop: asyncio.AbstractEventLoop
    ) -> AsyncGenerator[Chrome, None]:
        driver = None
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--incognito")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1980,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--enable-javascript")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-3d-apis")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.page_load_strategy = "none"

        try:
            with ThreadPoolExecutor() as pool:
                driver = await loop.run_in_executor(
                    pool,
                    self._run_driver,
                    {
                        "options": options,
                        "seleniumwire_options": {
                            "request_storage": "memory",
                            "request_storage_max_size": 1000,
                        },
                    },
                )
                driver.request_interceptor = self.__request_interceptor
                driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {
                        "source": """
                                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                            """
                    },
                )
            yield driver

        finally:
            if driver:
                driver.quit()

    async def _create_request(
        self, urls: Iterable[str], cookie: dict[str, str]
    ) -> tuple[httpx_Response, ...]:
        result = []
        task = []

        async with AsyncClient() as client:
            for url in urls:
                result.append(
                    asyncio.create_task(
                        client.get(
                            url=url,
                            cookies=cookie,
                        )
                    )
                )
            try:
                for item in await asyncio.gather(*task):
                    if item.status_code == 200:
                        result.append(item)
            except (RequestError, ReadTimeout, ConnectTimeout) as err:
                print(f"Произошла ошибка - {err}")

        return tuple(result)

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

    def __request_interceptor(self, request: sw_Request) -> None:
        if request.url == DNS_SHOP and (cookies := str(request.headers["Cookie"])):
            self.cookie[COOKIES_ARE] = cookies
            self.__time_sleep_done = False

    async def _driver_run(self, url: str) -> None:
        loop = asyncio.get_running_loop()

        async with self.get_driver(loop) as driver:
            driver.get(url)
            driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": self.ua.chrome})
            await asyncio.sleep(self.time_sleep_selenium)

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

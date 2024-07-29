from bs4 import BeautifulSoup
from contextlib import asynccontextmanager
from httpx import AsyncClient, RequestError, ReadTimeout, Response as httpx_Response, ConnectTimeout
from DrissionPage import ChromiumPage, ChromiumOptions
from typing import AsyncGenerator, Iterable, TypeVar

from constants import DNS_SHOP, COOKIES_ARE, SITEMAP_LINK

import asyncio


T = TypeVar("T", list[str], list[dict[str, str]])


class ParserDnsShop:

    def __init__(self) -> None:
        self.cookie: dict[str, str] = {COOKIES_ARE: ""}
        self.max_request = 24
        self.__auto_update_trigger = False
        self.__update_cookies_task = None
        self.__lock = asyncio.Lock()

    async def while_update_cookies(self) -> None:
        self.loop = asyncio.get_running_loop()

        while self.__auto_update_trigger:
            async with self.__lock:
                while not self.cookie[COOKIES_ARE]:
                    self.cookie[COOKIES_ARE] = await self.loop.run_in_executor(None, self.get_cookies)

            await asyncio.sleep(10 * 60)
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
            chrome_options = ChromiumOptions()

            chrome_options.set_argument(arg="--headless=new")
            chrome_options.set_argument(arg="--no-sandbox")
            chrome_options.set_argument(arg="--enable-javascript")
            chrome_options.set_argument(arg="--window-size=1920,1080")
            chrome_options.set_argument(arg="--disable-gpu")
            chrome_options.set_argument(arg="--ignore-certificate-errors")
            chrome_options.set_argument(arg="--disable-dev-shm-usage")
            chrome_options.set_argument(arg="--incognito")
            chrome_options.set_argument(arg="--disable-blink-features=AutomationControlled")
            chrome_options.set_argument(arg="--disable-3d-apis")
            chrome_options.set_argument(arg="--blink-settings=imagesEnabled=false")

            page = ChromiumPage(addr_or_opts=chrome_options)
            page.run_cdp_loaded(
                cmd="Page.addScriptToEvaluateOnNewDocument",
                source="""
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;,
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                """,
            )

            page.run_cdp_loaded(
                cmd="Network.setUserAgentOverride",
                userAgent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.3",
            )
            page.get(DNS_SHOP, timeout=20)

            cookies = page.cookies()
            cookie = "; ".join((f"{item['name']}={item['value']}" for item in cookies))

            page.quit()

            return cookie

        except Exception:
            return ""

    async def _create_request(self, urls: Iterable[str], cookie: dict[str, str]) -> tuple[httpx_Response, ...]:
        result = []

        async with self.__lock:
            async with AsyncClient() as client:
                tasks = [asyncio.create_task(client.get(url=url, cookies=cookie)) for url in urls]

                try:
                    for item in await asyncio.gather(*tasks):
                        if item.status_code == 200:
                            result.append(item)
                except (RequestError, ReadTimeout, ConnectTimeout) as err:
                    print(f"Произошла ошибка - {err}")

        return tuple(result)

    def _parse_xml(self, data: tuple[str, ...], sitemap: bool = False) -> list[str]:
        links = []

        for item in data:
            soup = BeautifulSoup(item, "xml")

            for link in soup.findAll("loc"):
                url_link = link.getText("", True)

                if url_link:
                    if sitemap:
                        if url_link.startswith("https://www.dns-shop.ru/products"):
                            links.append(url_link)

                    else:
                        links.append(url_link)

        return links

    def _parse_guid(self, data: tuple[httpx_Response, ...]) -> list[dict[str, str]]:
        result = []

        for item in data:
            soup = BeautifulSoup(item.text, "lxml")
            block = soup.find("div", {"class": "container product-card"})

            if block:
                result.append({"url": str(item.request.url), "guid": block["data-product-card"]})  # type: ignore

        return result

    async def get_all_links_product(self) -> list[str]:
        sitemap_response = await self._create_request((SITEMAP_LINK,), cookie=self.cookie)
        sitemap_links = await self.loop.run_in_executor(
            None, self._parse_xml, tuple(i.text for i in sitemap_response), True
        )

        products_response = await self._create_request(sitemap_links, cookie=self.cookie)
        products_links = await self.loop.run_in_executor(
            None, self._parse_xml, tuple(i.text for i in products_response)
        )

        return products_links

    async def __get_batch_request(self, data: T) -> AsyncGenerator[T, None]:

        for start in range(0, len(data), self.max_request):
            yield data[start : start + self.max_request]

    async def get_all_guid_product(self, data: list[str]) -> list[dict[str, str]]:
        result = []

        async for batch in self.__get_batch_request(data=data):

            response = await self._create_request(urls=batch, cookie=self.cookie)

            result.extend(self._parse_guid(data=response))

        return result

    async def get_all_info_product(self, data: list[dict[str, str]]) -> list[dict[str, str]]:
        response_data = {}

        async for batch in self.__get_batch_request(data=data):
            urls = []

            for item in batch:
                urls.append(f"https://www.dns-shop.ru/product/microdata/{item['guid']}/")

            response = await self._create_request(urls=urls, cookie=self.cookie)

            for item in response:
                if (data_resp := item.json()) and data_resp.get("result"):
                    response_data[data_resp["data"].get("offers", {}).get("url", str(item.request.url))] = {
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

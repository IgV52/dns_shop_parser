from asyncio import run
from time import monotonic, strftime, gmtime

from dns_shop_parser import ParserDnsShop


async def main() -> None:
    parser = ParserDnsShop(url="https://www.dns-shop.ru/")
    start = monotonic()

    async with parser.auto_update_cookies():
        links = await parser.get_all_links_product()
        data = await parser.get_all_guid_product(links[:1])
        result = await parser.get_all_info_product(data)

        print(f"Количество товаров - {len(result)}")

    end = monotonic() - start

    print(f"Время работы программы - {strftime('%H:%M:%S', gmtime(end))}")


if __name__ == "__main__":
    run(main())

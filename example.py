from parser_dns import ParserDnsShop

import asyncio
import time


async def main() -> None:
    parser = ParserDnsShop()
    start = time.monotonic()
    links = await parser.get_all_links_product()

    if links:
        data = await parser.get_all_guid_product(links[:25000])
        result = await parser.get_all_info_product(data)

        print(f"Количество товаров - {len(result)}")

    end = time.monotonic() - start

    print(f"Время работы программы - {time.strftime('%H:%M:%S', time.gmtime(end))}")


if __name__ == "__main__":
    asyncio.run(main())

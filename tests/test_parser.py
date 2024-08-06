from pytest import mark

from dns_shop_parser import ParserDnsShop


@mark.anyio
async def test_parser_complex(dns_shop_mock) -> None:
    parser = ParserDnsShop(url="http://test/")
    parser._client = dns_shop_mock
    parser.cookie = None

    links = await parser.get_all_links_product()
    assert 1 == len(links)

    data = await parser.get_all_guid_product(links)
    assert 1 == len(data)

    result = await parser.get_all_info_product(data)
    assert 1 == len(result)

from asyncio import get_running_loop
from pytest import fixture
from typing import AsyncGenerator, Literal
from httpx import AsyncClient, ASGITransport
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette.requests import Request
from os.path import abspath, dirname, join as os_join


async def get_assets(key: Literal["sitemap", "product", "products", "microdata"]) -> str:
    map_assets = {
        "sitemap": "sitemap.xml",
        "product": "product.html",
        "products": "products.xml",
        "microdata": "microdata.json",
    }

    def read_assets(filename: str) -> str:
        with open(os_join("/", dirname(abspath(__file__)), "assets", filename), mode="rb") as f:
            return f.read()

    loop = get_running_loop()
    filename = map_assets[key]
    return await loop.run_in_executor(None, read_assets, filename)


@fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@fixture(scope="session")
async def dns_shop_mock() -> AsyncGenerator[AsyncClient, None]:
    async def sitemap(request: Request) -> str:
        return HTMLResponse(content=await get_assets(key="sitemap"))

    async def microdata(request: Request) -> str:
        return HTMLResponse(content=await get_assets(key="microdata"))

    async def product(request: Request) -> str:
        return HTMLResponse(content=await get_assets(key="product"))

    async def products(request: Request) -> str:
        return HTMLResponse(content=await get_assets(key="products"))

    app = Starlette(
        routes=(
            Route("/sitemap.xml", sitemap),
            Route("/product", product),
            Route("/products.xml", products),
            Route("/product/microdata/00051854-bcb6-11ed-90ae-00155d8ed209", microdata),
        )
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as _client:
        yield _client

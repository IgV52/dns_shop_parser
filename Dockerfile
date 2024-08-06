FROM python:3.11.10-alpine3.20 AS module_dns_shop_parser

RUN pip install --upgrade pip && pip install build

WORKDIR /source_code

COPY ./dns_shop_parser ./dns_shop_parser
COPY ./pyproject.toml ./pyproject.toml
COPY ./requirements.txt ./requirements.txt

WORKDIR /

RUN python -m build /source_code && \
    mkdir /wheels/ && \
    cp /source_code/dist/dns_shop_parser-0.1-py3-none-any.whl /wheels/ && \
    rm -rf /source_code

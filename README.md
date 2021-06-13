<div align="center">

# Orkestra

### The elegance of Airflow + the power of AWS

[![Docs](https://img.shields.io/badge/Docs-mkdocs-blue?style=for-the-badge)](https://knowsuchagency.github.io/orkestra)
[![Codecov](https://img.shields.io/codecov/c/github/knowsuchagency/orkestra?style=for-the-badge)](https://app.codecov.io/gh/knowsuchagency/orkestra/)

[![PyPI](https://img.shields.io/pypi/v/orkestra)](https://pypi.org/project/orkestra/)
![PyPI - Downloads](https://img.shields.io/pypi/dw/orkestra)
![PyPI - License](https://img.shields.io/pypi/l/orkestra)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/orkestra)
![GitHub issues](https://img.shields.io/github/issues/knowsuchagency/orkestra)
[![Mentioned in Awesome CDK](https://awesome.re/mentioned-badge.svg)](https://github.com/kolomied/awesome-cdk)

[comment]: <> ([![codecov]&#40;https://codecov.io/gh/knowsuchagency/orkestra/branch/main/graph/badge.svg?token=DXFC1QP12O&#41;]&#40;https://codecov.io/gh/knowsuchagency/orkestra&#41;)



</div>

*examples/hello_orkestra.py*

```python
import random
from typing import *
from uuid import uuid4

from aws_lambda_powertools import Logger, Tracer
from pydantic import BaseModel

from orkestra import compose
from orkestra.interfaces import Duration


def dag():
    (
        generate_item
        >> add_price
        >> copy_item
        >> double_price
        >> (do_nothing, assert_false)
        >> say_hello
        >> [random_int, random_float]
        >> say_goodbye
    )


class Item(BaseModel):
    id: str
    name: str
    price: Optional[float] = None

    @classmethod
    def random(cls):
        return cls(
            id=str(uuid4()),
            name=random.choice(
                [
                    "potato",
                    "moon rock",
                    "hat",
                ]
            ),
        )


logger = Logger()

tracer = Tracer()


default_args = dict(
    enable_powertools=True,
    timeout=Duration.seconds(6),
)


@compose(**default_args)
def generate_item(event, context):
    logger.info("generating random item")
    item = Item.random().dict()
    logger.info(item)
    tracer.put_metadata("GenerateItem", "SUCCESS")
    return item


@compose(model=Item, **default_args)
def add_price(item: Item, context):
    price = 3.14
    logger.info(
        "adding price to item",
        extra={
            "item": item.dict(),
            "price": price,
        },
    )
    item.price = price
    return item.dict()


@compose(model=Item, **default_args)
def copy_item(item: Item, context) -> list:
    logger.info(item.dict())
    return [item.dict()] * 10


@compose(model=Item, is_map_job=True, **default_args)
def double_price(item: Item, context):
    item.price = item.price * 2
    return item.dict()


@compose(**default_args)
def assert_false(event, context):
    assert False


@compose(**default_args)
def do_nothing(event, context):
    logger.info({"doing": "nothing"})


@compose(**default_args)
def say_hello(event, context):
    return "hello, world"


@compose(**default_args)
def say_goodbye(event, context):
    return "goodbye"


@compose(**default_args)
def random_int(event, context):
    return random.randrange(100)


@compose(**default_args)
def random_float(event, context):
    return float(random_int(event, context))


dag()
```

*app.py*

```python
#!/usr/bin/env python3
from aws_cdk import core as cdk

from examples.hello_orkestra import generate_item


class HelloOrkestra(cdk.Stack):
    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        generate_item.schedule(
            self,
            expression="rate(5 minutes)",
            state_machine_name="hello_orkestra",
        )


app = cdk.App()


app.synth()
```

![state machine](https://github.com/knowsuchagency/orkestra/blob/main/docs/assets/images/hello_orkestra_sfn.png?raw=true)

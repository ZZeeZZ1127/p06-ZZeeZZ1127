# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

import asyncio
from io import BytesIO

from PIL import Image

from thumbor.config import Config
from thumbor.context import Context, RequestParameters
from thumbor.engines.pil import Engine
from thumbor.importer import Importer
from thumbor.transformer import Transformer

RAINBOW = "rainbow.png"
WIDE = "940x2.png"


def get_context():
    cfg = Config(
        SECURITY_KEY="ACME-SEC",
        ENGINE="thumbor.engines.pil",
        LOADER="thumbor.loaders.file_loader",
        FILE_LOADER_ROOT_PATH="course/images",
    )
    importer = Importer(cfg)
    importer.import_modules()
    return Context(config=cfg, importer=importer)


def run_transform(image, width, height, fit_in=False):
    context = get_context()
    context.request = RequestParameters(
        width=width, height=height, fit_in=fit_in, image=image
    )
    engine = Engine(context)
    engine.extension = ".png"
    with open(f"course/images/{image}", "rb") as image_file:
        engine.load(image_file.read(), ".png")
    context.request.engine = engine

    asyncio.run(Transformer(context).transform())
    return engine


def test_extreme_wide_request_is_not_empty():
    # rainbow.png is a 16x16 transparent PNG with coloured bars. Requesting
    # it at an aspect ratio far from the source must still return a real
    # picture, not an all-transparent image.
    engine = run_transform(RAINBOW, 800, 20)

    output = Image.open(BytesIO(engine.read(".png")))
    assert output.size == (800, 20)
    rgba = output.convert("RGBA")
    # The coloured bars must survive: at least some fully opaque pixels.
    assert max(rgba.getchannel("A").getextrema()) > 0


def test_fit_in_1x1_very_wide_source():
    # A very wide source fit into a 1x1 box must not blow up.
    engine = run_transform(WIDE, 1, 1, fit_in=True)
    output = Image.open(BytesIO(engine.read(".png")))
    assert output.size[0] >= 1
    assert output.size[1] >= 1


def test_fit_in_width_only_very_wide_source():
    # A width-only fit-in request on a very wide source must not blow up.
    engine = run_transform(WIDE, 100, 0, fit_in=True)
    output = Image.open(BytesIO(engine.read(".png")))
    assert output.size == (100, 1)

# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from io import BytesIO
from os.path import abspath, dirname, join

from PIL import Image

from thumbor.config import Config
from thumbor.context import Context
from thumbor.engines.pil import Engine

FIXTURES_PATH = abspath(join(dirname(__file__), "fixtures/"))
STORAGE_PATH = join(FIXTURES_PATH, "images")


def get_context():
    cfg = Config(
        SECURITY_KEY="ACME-SEC",
        ENGINE="thumbor.engines.pil",
        IMAGE_METADATA_READ_FORMATS="exif,xmp",
    )
    cfg.LOADER = "thumbor.loaders.file_loader"
    cfg.FILE_LOADER_ROOT_PATH = STORAGE_PATH
    cfg.STORAGE = "thumbor.storages.no_storage"
    return Context(config=cfg)


def load_engine(path, extension):
    engine = Engine(get_context())
    engine.extension = extension
    with open(path, "rb") as image_file:
        engine.load(image_file.read(), extension)
    return engine


class TestGifPaletteTransparency:
    def test_resize_keeps_gif_transparency(self):
        # sticker.gif is a palette GIF that marks one palette entry as
        # transparent. Resizing it and writing it back out as GIF must keep
        # those pixels transparent; before the fix the re-quantization in
        # Engine.read() dropped the transparency index and the transparent
        # background came back as a solid black box.
        path = join("course", "images", "sticker.gif")
        source = Image.open(path)
        assert source.mode == "P"
        assert source.info.get("transparency") == 0

        engine = load_engine(path, ".gif")
        engine.resize(240, 160)
        result = engine.read(".gif")

        output = Image.open(BytesIO(result))
        assert "transparency" in output.info

        alpha = output.convert("RGBA").getchannel("A")
        # A transparent background means at least one fully transparent pixel
        # and at least one fully opaque pixel.
        assert min(alpha.getextrema()) == 0
        assert max(alpha.getextrema()) == 255

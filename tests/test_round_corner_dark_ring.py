# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from tornado.testing import gen_test

from tests.base import FilterTestCase


class RoundCornerDarkRingTestCase(FilterTestCase):
    @gen_test
    async def test_transparent_round_corner_has_no_dark_ring(self):
        # A transparent round corner must fade its anti-aliased arc through
        # the alpha channel: edge pixels keep their colour and lose alpha.
        # Before the fix those pixels were scaled towards black while staying
        # fully opaque, producing a dark ring along the curve.
        image = await self.get_filtered(
            "source.jpg",
            "thumbor.filters.round_corner",
            "round_corner(50,255,255,255,1)",
            mode="RGBA",
        )

        assert image.mode == "RGBA"
        pixels = image.load()

        radius = 50
        dark_ring_pixels = 0
        for y in range(radius + 2):
            for x in range(radius + 2):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    # Fully removed: outside the rounded shape.
                    continue
                # A pixel that is still opaque but almost black is the ring.
                if a == 255 and r < 16 and g < 16 and b < 16:
                    dark_ring_pixels += 1

        assert dark_ring_pixels == 0, (
            f"found {dark_ring_pixels} dark, fully opaque pixels on the "
            "anti-aliased arc"
        )

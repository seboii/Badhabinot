import base64
import json
import struct
import zlib


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def build_png(width: int = 128, height: int = 128) -> bytes:
    raw_rows = bytearray()
    for y in range(height):
        raw_rows.append(0)
        for x in range(width):
            red = 180
            green = min(255, 80 + x)
            blue = min(255, 80 + y)
            raw_rows.extend((red, green, blue))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw_rows), level=9)
    signature = b"\x89PNG\r\n\x1a\n"
    return signature + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")


if __name__ == "__main__":
    png_bytes = build_png()
    print(
        json.dumps(
            {
                "image_base64": base64.b64encode(png_bytes).decode("ascii"),
                "image_content_type": "image/png",
            }
        )
    )

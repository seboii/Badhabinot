import base64
import json


def build_ppm(width: int = 128, height: int = 128) -> bytes:
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            red = 180
            green = min(255, 80 + x)
            blue = min(255, 80 + y)
            pixels.extend((red, green, blue))
    return header + bytes(pixels)


if __name__ == "__main__":
    ppm_bytes = build_ppm()
    print(
        json.dumps(
            {
                "image_base64": base64.b64encode(ppm_bytes).decode("ascii"),
                "image_content_type": "image/x-portable-pixmap",
            }
        )
    )

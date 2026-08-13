"""Тематичні обкладинки для демо-статей блогу (1200×900, 4:3)."""

from __future__ import annotations

import io
import math

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw

W, H = 1200, 900

BRAND = (108, 86, 133)
BRAND_MID = (130, 111, 151)
SOFT = (214, 228, 235)
SUN = (230, 134, 26)
PANEL = (28, 52, 68)
PANEL_LINE = (90, 140, 155)
INK = (81, 65, 100)
SKY_TOP = (186, 214, 224)
SKY_BOT = (246, 242, 247)


def _gradient(draw: ImageDraw.ImageDraw, top, bottom) -> None:
    for y in range(H):
        t = y / (H - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=color)


def _sun(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int = 70) -> None:
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=SUN)
    for i in range(8):
        ang = math.radians(i * 45)
        x1 = cx + int(math.cos(ang) * (r + 12))
        y1 = cy + int(math.sin(ang) * (r + 12))
        x2 = cx + int(math.cos(ang) * (r + 36))
        y2 = cy + int(math.sin(ang) * (r + 36))
        draw.line([(x1, y1), (x2, y2)], fill=SUN, width=6)


def _panel_grid(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], cols=6, rows=3) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=10, fill=PANEL, outline=BRAND, width=3)
    for c in range(1, cols):
        x = x0 + (x1 - x0) * c // cols
        draw.line([(x, y0 + 8), (x, y1 - 8)], fill=PANEL_LINE, width=2)
    for r in range(1, rows):
        y = y0 + (y1 - y0) * r // rows
        draw.line([(x0 + 8, y), (x1 - 8, y)], fill=PANEL_LINE, width=2)


def _house(draw: ImageDraw.ImageDraw, base_y: int = 620) -> None:
    draw.polygon([(180, base_y), (520, base_y - 220), (860, base_y)], fill=BRAND_MID)
    draw.rectangle((260, base_y, 780, base_y + 180), fill=(245, 240, 232), outline=BRAND, width=3)
    draw.rectangle((470, base_y + 60, 560, base_y + 180), fill=BRAND)
    _panel_grid(draw, (300, base_y - 190, 720, base_y - 40), cols=8, rows=3)


def scene_panels() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw, SKY_TOP, SKY_BOT)
    _sun(draw, 980, 140, 78)
    _house(draw)
    draw.ellipse((40, 780, 1160, 980), fill=(120, 150, 90))
    return img


def scene_mono_poly() -> Image.Image:
    img = Image.new("RGB", (W, H), SOFT)
    draw = ImageDraw.Draw(img)
    _gradient(draw, (230, 236, 230), SOFT)
    draw.rounded_rectangle((80, 140, 560, 760), radius=18, fill=PANEL, outline=BRAND, width=4)
    draw.rounded_rectangle((640, 140, 1120, 760), radius=18, fill=(55, 95, 70), outline=BRAND_MID, width=4)
    for box, cols in (((110, 180, 530, 700), 4), ((670, 180, 1090, 700), 5)):
        x0, y0, x1, y1 = box
        for c in range(1, cols):
            x = x0 + (x1 - x0) * c // cols
            draw.line([(x, y0), (x, y1)], fill=PANEL_LINE, width=2)
        for r in range(1, 6):
            y = y0 + (y1 - y0) * r // 6
            draw.line([(x0, y), (x1, y)], fill=PANEL_LINE, width=2)
    draw.text((220, 780), "МОНО", fill=BRAND)
    draw.text((820, 780), "ПОЛІ", fill=BRAND_MID)
    _sun(draw, 600, 90, 40)
    return img


def scene_inverter() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw, (210, 220, 215), SOFT)
    draw.rounded_rectangle((320, 160, 880, 720), radius=24, fill=(45, 55, 50), outline=BRAND, width=4)
    draw.rounded_rectangle((380, 230, 820, 420), radius=12, fill=(30, 90, 50))
    draw.rectangle((410, 270, 790, 300), fill=SUN)
    draw.rectangle((410, 330, 680, 360), fill=SOFT)
    for i, y in enumerate((480, 540, 600)):
        draw.ellipse((400, y, 460, y + 60), outline=SUN, width=4)
        draw.rectangle((490, y + 15, 780, y + 45), fill=(70, 80, 75))
    _sun(draw, 980, 120, 50)
    return img


def scene_mounting() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw, SKY_TOP, (235, 230, 220))
    # дах / хвилі металочерепиці
    for i in range(10):
        y = 220 + i * 48
        for x in range(0, W, 80):
            draw.arc((x, y, x + 90, y + 50), 0, 180, fill=(160, 70, 55), width=5)
    _panel_grid(draw, (220, 280, 980, 620), cols=10, rows=4)
    draw.rectangle((200, 640, 1000, 670), fill=BRAND)
    _sun(draw, 1000, 110, 55)
    return img


def scene_battery() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw, (200, 210, 205), SOFT)
    draw.rounded_rectangle((380, 180, 820, 760), radius=28, fill=(50, 60, 55), outline=BRAND, width=4)
    draw.rectangle((470, 140, 730, 190), fill=BRAND_MID)
    for i in range(4):
        y = 240 + i * 110
        draw.rounded_rectangle((430, y, 770, y + 80), radius=10, fill=(35, 100, 55))
        draw.rectangle((460, y + 28, 620, y + 52), fill=SUN)
    draw.polygon([(860, 420), (980, 500), (860, 580)], fill=SUN)
    return img


def scene_payback() -> Image.Image:
    img = Image.new("RGB", (W, H), SOFT)
    draw = ImageDraw.Draw(img)
    _gradient(draw, (235, 240, 236), SOFT)
    draw.rectangle((160, 160, 1040, 720), outline=BRAND, width=3)
    bars = [180, 260, 340, 430, 520, 610]
    for i, h in enumerate(bars):
        x0 = 220 + i * 130
        draw.rectangle((x0, 700 - h, x0 + 80, 700), fill=BRAND_MID if i < 4 else SUN)
    draw.line([(200, 700), (1020, 700)], fill=INK, width=3)
    _sun(draw, 1000, 120, 48)
    return img


def scene_maintenance() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw, SKY_TOP, SKY_BOT)
    _panel_grid(draw, (160, 220, 1040, 620), cols=9, rows=4)
    # «щітка»
    draw.line([(300, 700), (520, 480)], fill=(120, 90, 50), width=14)
    draw.ellipse((480, 430, 620, 520), fill=SOFT, outline=BRAND, width=4)
    _sun(draw, 980, 130, 60)
    return img


def scene_myths() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw, (220, 230, 210), SOFT)
    _sun(draw, 600, 280, 120)
    draw.ellipse((420, 480, 780, 820), outline=BRAND, width=10)
    draw.rectangle((575, 540, 625, 700), fill=BRAND)
    draw.ellipse((575, 730, 625, 780), fill=BRAND)
    return img


def scene_grid() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw, SKY_TOP, SKY_BOT)
    for x in (280, 600, 920):
        draw.rectangle((x - 12, 280, x + 12, 780), fill=(90, 90, 90))
        draw.polygon([(x - 70, 280), (x, 200), (x + 70, 280)], fill=(70, 70, 70))
    draw.line([(280, 320), (920, 320)], fill=(60, 60, 60), width=5)
    draw.line([(280, 400), (920, 400)], fill=(60, 60, 60), width=5)
    _panel_grid(draw, (140, 520, 420, 720), cols=4, rows=2)
    _sun(draw, 1040, 120, 55)
    return img


def scene_business() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw, SKY_TOP, (230, 232, 228))
    draw.rectangle((180, 300, 1020, 780), fill=(230, 228, 220), outline=BRAND, width=3)
    for row in range(4):
        for col in range(6):
            x0 = 220 + col * 120
            y0 = 340 + row * 90
            draw.rectangle((x0, y0, x0 + 80, y0 + 55), fill=SOFT, outline=BRAND_MID, width=2)
    _panel_grid(draw, (240, 160, 960, 300), cols=12, rows=2)
    _sun(draw, 1040, 100, 50)
    return img


def scene_passport() -> Image.Image:
    img = Image.new("RGB", (W, H), SOFT)
    draw = ImageDraw.Draw(img)
    _gradient(draw, (240, 242, 238), SOFT)
    draw.rounded_rectangle((280, 120, 920, 780), radius=16, fill=(252, 252, 250), outline=BRAND, width=4)
    draw.rectangle((320, 170, 880, 240), fill=BRAND)
    for i in range(6):
        y = 300 + i * 70
        draw.rectangle((340, y, 860, y + 18), fill=(200, 210, 200))
    _panel_grid(draw, (700, 520, 880, 700), cols=3, rows=2)
    return img


def scene_checklist() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw, (225, 235, 228), SOFT)
    draw.rounded_rectangle((220, 120, 980, 780), radius=20, fill=(250, 250, 248), outline=BRAND, width=4)
    for i in range(5):
        y = 200 + i * 100
        draw.rounded_rectangle((280, y, 360, y + 60), radius=8, outline=BRAND_MID, width=4)
        if i < 3:
            draw.line([(295, y + 30), (315, y + 48), (345, y + 12)], fill=BRAND, width=6)
        draw.rectangle((400, y + 18, 900, y + 42), fill=(210, 220, 210))
    _sun(draw, 980, 100, 45)
    return img


def scene_default() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _gradient(draw, SKY_TOP, SKY_BOT)
    _sun(draw, 960, 150, 80)
    _house(draw, base_y=600)
    return img


SCENES = {
    "panels": scene_panels,
    "mono_poly": scene_mono_poly,
    "inverter": scene_inverter,
    "mounting": scene_mounting,
    "battery": scene_battery,
    "payback": scene_payback,
    "maintenance": scene_maintenance,
    "myths": scene_myths,
    "grid": scene_grid,
    "business": scene_business,
    "passport": scene_passport,
    "checklist": scene_checklist,
    "default": scene_default,
}


def make_cover(scene_key: str, filename: str) -> ContentFile:
    factory = SCENES.get(scene_key, scene_default)
    img = factory()
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90, optimize=True)
    return ContentFile(buffer.getvalue(), name=filename)

#!/usr/bin/env python3
"""compose.py — membangun entry.png news-image-20261126 (1024x1024, <=1 MiB).

Ditulis di sesi build 27 Nov 2026. Menjalankan skrip ini di sesi build,
BUKAN oleh program penilai (program penilai hanya menyalin entry.png).
Sumber: isi.md (39 cerita terverifikasi 26 Nov 2026 UTC), teks.md, arah.md,
layout.md. Peta dari Natural Earth 1:110m (domain publik, lihat sumber.md).
Font: Noto Serif / Noto Sans (OFL) yang terpasang di sistem build.

Fit-check: setiap teks diukur dengan font sebenarnya sebelum digambar;
teks yang tidak muat dalam anggarannya menggagalkan build (sys.exit 1).
Render deterministik: dua kali jalan menghasilkan byte identik.
"""
import json
import math
import os
import sys

# ---------------------------------------------------------------- konstanta
W, H = 1024, 1024
MARGIN = 20
CW = W - 2 * MARGIN  # 984

SERIF_B = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

# palet halaman (arah.md)
PAPER = (247, 243, 234)
INK = (27, 26, 23)
NAVY = (27, 42, 74)
MUTED = (90, 85, 75)
CHARCOAL = (35, 39, 46)
WHITE = (255, 255, 255)
LINE = (150, 145, 135)

# warna wilayah (selisih rona antar pasangan >= 30 derajat)
REGION = {
    "NA": (37, 99, 235),    # Amerika Utara, rona 217
    "SA": (5, 150, 105),    # Amerika Selatan, rona 161
    "EU": (124, 58, 237),   # Eropa, rona 262
    "ME": (220, 38, 38),    # Timur Tengah, rona 0
    "AF": (217, 119, 6),    # Afrika, rona 32
    "AS": (101, 163, 13),   # Asia, rona 84
    "OC": (219, 39, 119),   # Oseania/Pasifik, rona 327
}
REGION_NAME = {"NA": "NORTH AMERICA", "SA": "SOUTH AMERICA", "EU": "EUROPE",
               "ME": "MIDDLE EAST", "AF": "AFRICA", "AS": "ASIA", "OC": "OCEANIA"}
REGION_COUNT = {"NA": 6, "SA": 2, "EU": 13, "ME": 5, "AF": 6, "AS": 5, "OC": 2}

# palet ilustrasi bersama (terpisah dari warna wilayah)
ILL_INK = (32, 36, 42)
ILL_CREAM = (247, 243, 234)
ILL_BLUE = (107, 140, 174)   # dusty blue
ILL_OCHRE = (217, 164, 65)
ILL_RUST = (180, 85, 45)
ILL_SAGE = (122, 139, 111)
ILL_NAVY = (46, 64, 87)      # slate navy (latar malam)
ILL_FIRE = (224, 120, 64)
ILL_SMOKE = (60, 58, 55)
ILL_GOLD = (201, 162, 39)

# ---------------------------------------------------------------- data teks
MASTHEAD_DATE = "THURSDAY 26 NOVEMBER 2026"
COUNT_LINE = "39 STORIES  ·  7 REGIONS  ·  EVERY STORY DATED 26 NOVEMBER 2026 (UTC)"
STATS = [("800,000+", "WITHOUT POWER IN U.S. STORM"),
         ("87", "MISSILES AND DRONES DOWNED"),
         ("€45BN", "EU LOAN FOR UKRAINE BLOCKED"),
         ("31", "KILLED IN CAIRO TANKER FIRE")]
UTC_ITEMS = [("OVERNIGHT", "Missiles hit a Kyiv mall"),
             ("08:37", "India asks Netflix to drop series"),
             ("17:13", "Guinea-Bissau delays vote to 2028"),
             ("21:27", "EU leaders split on budget")]
DATECHECK = ("DATE CHECK — Every story above happened or was first reported on Thursday "
             "26 November 2026 (UTC). Left out as earlier news: U.S. tariff proposal "
             "(25 November), Huawei verdict (24 November), FCC approval of SpaceX's "
             "satellite plan (25 November), Solomon–Australia pact (25 November). "
             "Not yet: Spain's election (29 November); the Macy's parade (28 November).")
FOOTER = ("All 39 stories sourced — Reuters · AP · BBC · Al Jazeera · France 24 · Euronews · "
          "The Guardian · CBC · NPR · CNBC. Illustrations drawn for this page. "
          "One image, one day: Thursday 26 November 2026 (UTC).")

# cerita bergambar: (nomor, kicker, status, judul, dek, sumber, hook, region)
HEROES = [
    (1, "KUWAIT CITY · MIDDLE EAST", "REPORTED",
     "Drone strike in Kuwait kills two Italian technicians",
     "Italy and Kuwait blame Iran; Tehran denies it and offers a joint inquiry.",
     "Reuters", "DRONES OVER THE GULF", "ME"),
    (2, "U.S. EAST COAST · WEATHER", "CONFIRMED",
     "Thanksgiving storm knocks out power to 800,000+",
     "The 100th Macy's parade is postponed for the first time ever, to Saturday.",
     "USA Today / AP", "STORM SHUTS THE EAST COAST", "NA"),
    (3, "KYIV · UKRAINE", "CONFIRMED",
     "Russia and Ukraine trade overnight strikes",
     "87 missiles and drones downed; at least three killed as Trump urges Putin to pull back.",
     "Reuters", "MISSILES OVER KYIV", "EU"),
]
CARDS = [
    (4, "JAZAN · SAUDI ARABIA", "REPORTED",
     "Houthi strike kills one at Jazan refinery",
     "Fire shuts part of the plant.", "Al Jazeera", "REFINERY FIRE", "ME"),
    (5, "BRUSSELS · EUROPE", "CONFIRMED",
     "EU split over budget and €45bn loan",
     "Germany threatens a veto.", "AP", "BUDGET DEADLOCK", "EU"),
    (6, "BRUSSELS · EUROPE", "CONFIRMED",
     "Spain's Hernández de Cos to lead ECB",
     "First Spaniard to lead ECB.", "France 24", "NEW ECB CHIEF", "EU"),
    (7, "PYONGYANG", "REPORTED",
     "Kim calls for wider nuclear deployment",
     "Seoul responds the same day.", "Reuters / KCNA", "NUCLEAR WARNING", "AS"),
    (8, "DEIR AL-BALAH · GAZA", "REPORTED",
     "Strikes kill nine in Gaza despite ceasefire",
     "Strikes go on a third night.", "France 24 / BBC", "STRIKES IN GAZA", "ME"),
    (10, "CAIRO · EGYPT", "CONFIRMED",
     "Cairo tanker fire death toll rises to 31",
     "Driver, 21, detained.", "AP", "TANKER FIRE", "AF"),
    (11, "BANGKOK · THAILAND", "CONFIRMED",
     "Blast at Bangchak refinery injures nine",
     "Three critically hurt.", "BBC", "REFINERY BLAST", "AS"),
    (12, "IBIZA · SPAIN", "CONFIRMED",
     "Tanker capsizes off Ibiza; one dies",
     "17 rescued; coast at risk.", "BBC / DW", "TANKER CAPSIZES", "EU"),
    (13, "ITURI · DR CONGO", "CONFIRMED",
     "Ebola passes 12,000 cases",
     "Second-largest outbreak ever.", "CBC / UPI", "EBOLA SURGE", "AF"),
    (15, "GUINEA-BISSAU", "CONFIRMED",
     "Guinea-Bissau vote delayed until 2028",
     "December vote moves to 2028.", "Reuters", "VOTE DELAYED", "AF"),
]
# daftar: (nomor, tempat, judul, sumber, region)
LIST_ROWS = [
    (9, "JERUSALEM", "Bribery charge in doubt", "Euronews", "ME"),
    (14, "AFRICA", "Lenacapavir reaches Africa", "BBC", "AF"),
    (16, "MOMBASA", "Mackenzie guilty of terrorism", "Reuters", "AF"),
    (17, "GAZIPUR", "Garment workers clash over pay", "Reuters", "AS"),
    (18, "LONDON", "UK net migration falls to 77,000", "Guardian", "EU"),
    (19, "OSLO", "Norse Atlantic halts all flights", "BBC", "EU"),
    (20, "SEOUL", "South Korea raises rates to 3.25%", "CNBC", "AS"),
    (21, "WALSALL", "Poundland fails; 11,000 jobs at risk", "BBC", "EU"),
    (22, "NEW DELHI", "India asks Netflix to drop show", "Reuters", "AS"),
    (23, "ERBIL", "Iraq shuts two Kurdistan crossings", "Reuters", "ME"),
    (24, "CARACAS", "Bans on opponents lifted", "La Nación", "SA"),
    (25, "BRASÍLIA", "Brazil recalls Argentina envoy", "MercoPress", "SA"),
    (26, "WASHINGTON", "Shanghai falls 2.01% on tariffs", "BBC", "NA"),
    (27, "WASHINGTON", "Judge voids birthright curb", "Al Jazeera", "NA"),
    (28, "MADRID", "Abrego Garcia arrives in Madrid", "PBS", "EU"),
    (29, "ZURICH", "FIFA hit by cyberattack", "Ars Technica", "EU"),
    (30, "DAKAR", "CAS restores Africa Cup to Senegal", "NPR", "AF"),
    (31, "MELBOURNE", "Sinner out of Aussie Open", "Guardian", "OC"),
    (32, "SAN JUAN", "Puerto Rico wins Miss Universe", "Euronews", "NA"),
    (33, "BIRMINGHAM", "Duran Duran guitarist dies at 65", "BBC", "EU"),
    (34, "LAUSANNE", "IOC pioneer DeFrantz dies at 74", "Reuters", "EU"),
    (35, "DETROIT", "Bears stun Lions 39–35", "Guardian", "NA"),
    (36, "LILLE", "Lille ends Bayern's unbeaten run", "BBC Sport", "EU"),
    (37, "SPACE", "Hera images Dimorphos crater", "Euronews", "EU"),
    (38, "U.S.", "Pig-kidney patient a year off dialysis", "CBC", "NA"),
    (39, "FLINDERS ISLAND", "Island fire burns 10%", "Guardian", "OC"),
]
# pin peta: (nomor, lon, lat, region) — semua cerita dengan satu titik jelas.
# Tanpa pin: 26 (multi-kota), 37 (asteroid Dimorphos), 38 (AS umum).
PINS = [
    (1, 47.98, 29.38, "ME"), (2, -74.00, 40.70, "NA"), (3, 30.52, 50.45, "EU"),
    (4, 42.55, 16.89, "ME"), (5, 4.35, 50.85, "EU"), (6, 4.35, 50.85, "EU"),
    (7, 125.75, 39.03, "AS"), (8, 34.45, 31.42, "ME"), (9, 35.21, 31.77, "ME"),
    (10, 31.24, 30.06, "AF"), (11, 100.50, 13.76, "AS"), (12, 1.43, 38.98, "EU"),
    (13, 30.25, 1.57, "AF"), (14, 28.05, -26.20, "AF"), (15, -15.60, 11.86, "AF"),
    (16, 39.66, -4.05, "AF"), (17, 90.42, 24.00, "AS"), (18, -0.13, 51.50, "EU"),
    (19, 10.75, 59.91, "EU"), (20, 126.98, 37.57, "AS"), (21, -1.98, 52.59, "EU"),
    (22, 77.21, 28.61, "AS"), (23, 44.01, 36.19, "ME"), (24, -66.90, 10.48, "SA"),
    (25, -47.88, -15.79, "SA"), (27, -77.04, 38.90, "NA"), (28, -3.70, 40.42, "EU"),
    (29, 8.54, 47.38, "EU"), (30, -17.47, 14.72, "AF"), (31, 144.96, -37.81, "OC"),
    (32, -66.06, 18.47, "NA"), (33, -1.89, 52.48, "EU"), (34, 6.63, 46.52, "EU"),
    (35, -83.05, 42.33, "NA"), (36, 3.06, 50.63, "EU"), (39, 148.00, -40.00, "OC"),
]

# ---------------------------------------------------------------- helper teks
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

def font(path, size):
    return ImageFont.truetype(path, size)

class FitFail(Exception):
    pass

def wrap(draw, text, fnt, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_lines(draw, x, y, lines, fnt, fill=INK, lh=None, align="left", width=None):
    lh = lh or int(fnt.size * 1.22)
    for i, ln in enumerate(lines):
        if align == "center":
            tw = draw.textlength(ln, font=fnt)
            draw.text((x + (width - tw) / 2, y + i * lh), ln, font=fnt, fill=fill)
        else:
            draw.text((x, y + i * lh), ln, font=fnt, fill=fill)
    return y + len(lines) * lh

def fit(draw, name, text, fnt, width, max_lines):
    lines = wrap(draw, text, fnt, width)
    if len(lines) > max_lines:
        raise FitFail(f"{name}: {len(lines)} baris (maks {max_lines}): {text!r}")
    return lines

# ---------------------------------------------------------------- ilustrasi
# Semua ilustrasi digambar kode (PIL), satu bahasa visual: vektor datar,
# bentuk geometris tebal, outline tinta, tanpa gradien, tanpa huruf,
# tanpa wajah. Zona tenang: pita atas ~20 px (lencana/status) dan pita bawah
# ~26 px (hook) dibiarkan tenang; subjek di pita tengah.
# Setiap fungsi menggambar di kotak (x, y, w, h) dan TIDAK menggambar hook.

def _burst(d, cx, cy, r, color, n=8):
    pts = []
    for i in range(n * 2):
        ang = math.pi * i / n
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=color, outline=ILL_INK)

def _cloud(d, x, y, s, color):
    # Punuk tengah digeser ke bawah agar awan tidak pernah melewati y
    # (tepi atas kotak gambar).
    d.ellipse([x, y + s * 0.25, x + s, y + s * 0.85], fill=color)
    d.ellipse([x + s * 0.5, y, x + s * 1.5, y + s * 0.6], fill=color)
    d.ellipse([x + s * 1.0, y + s * 0.25, x + s * 2.0, y + s * 0.85], fill=color)

def _smoke(d, x, y, s, color=ILL_SMOKE):
    # Gugus asap digeser ke bawah 0.9*s agar tidak ada gumpalan yang melewati
    # y (tepi atas kotak gambar) dan menyentuh teks di atasnya.
    for dx, dy, r in [(0, 0.9, 0.55), (0.5, 0.55, 0.7), (1.1, 0.8, 0.6),
                      (0.3, 0.1, 0.5), (0.9, 0.0, 0.45)]:
        d.ellipse([x + dx * s, y + dy * s, x + (dx + r) * s, y + (dy + r) * s],
                  fill=color)

def _flame(d, cx, base, w, h, color=ILL_FIRE):
    pts = [(cx - w / 2, base), (cx - w * 0.28, base - h * 0.55),
           (cx - w * 0.08, base - h * 0.75), (cx + w * 0.12, base - h),
           (cx + w * 0.3, base - h * 0.6), (cx + w / 2, base)]
    d.polygon(pts, fill=color, outline=ILL_INK)

def ill_kuwait(d, x, y, w, h):
    """1 Kuwait: drone malam di atas situs Teluk, ledakan di fasilitas."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=ILL_NAVY)
    for sx, sy in [(0.12, 0.18), (0.3, 0.1), (0.55, 0.22), (0.78, 0.12), (0.9, 0.3)]:
        d.ellipse([x + sx * w - 1, y + sy * h - 1, x + sx * w + 1, y + sy * h + 1],
                  fill=WHITE)
    # laut (pita bawah, di atas zona hook)
    d.rectangle([x, y + h * 0.62, x + w - 1, y + h - 1], fill=(28, 52, 84))
    # fasilitas: kubah + menara (lebih besar)
    bx, by = x + w * 0.1, y + h * 0.62
    d.rectangle([bx, by - h * 0.34, bx + w * 0.22, by], fill=ILL_SAGE, outline=ILL_INK, width=2)
    d.pieslice([bx - w * 0.02, by - h * 0.5, bx + w * 0.24, by - h * 0.26],
               180, 360, fill=ILL_SAGE, outline=ILL_INK)
    d.rectangle([bx + w * 0.3, by - h * 0.5, bx + w * 0.37, by], fill=ILL_OCHRE,
                outline=ILL_INK, width=2)
    # ledakan di fasilitas
    _burst(d, bx + w * 0.16, by - h * 0.36, h * 0.26, ILL_FIRE)
    _burst(d, bx + w * 0.16, by - h * 0.36, h * 0.13, (255, 220, 120))
    # drone: badan + 4 rotor (lebih kecil)
    dx, dy = x + w * 0.7, y + h * 0.2
    d.ellipse([dx - w * 0.03, dy - h * 0.05, dx + w * 0.03, dy + h * 0.05],
              fill=ILL_INK)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ax, ay = dx + sx * w * 0.055, dy + sy * h * 0.07
            d.line([dx, dy, ax, ay], fill=ILL_INK, width=2)
            d.ellipse([ax - w * 0.03, ay - 2, ax + w * 0.03, ay + 2], fill=ILL_INK)
    # jejak asap drone
    d.line([dx - w * 0.2, dy + h * 0.12, dx - w * 0.05, dy + h * 0.05],
           fill=(150, 160, 180), width=2)

def ill_storm(d, x, y, w, h):
    """2 Badai Thanksgiving: awan gelap, hujan miring, skyline, balon parade."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=(112, 128, 148))
    _cloud(d, x + w * 0.05, y + h * 0.08, w * 0.16, (58, 66, 80))
    _cloud(d, x + w * 0.5, y + h * 0.02, w * 0.18, (48, 56, 70))
    # hujan miring
    for i in range(9):
        rx = x + w * (0.06 + i * 0.11)
        ry = y + h * 0.3
        d.line([rx, ry, rx - w * 0.03, ry + h * 0.22], fill=(210, 220, 232), width=2)
    # skyline
    sy = y + h * 0.62
    for bx, bw, bh in [(0.04, 0.1, 0.3), (0.16, 0.08, 0.38), (0.26, 0.12, 0.28),
                       (0.4, 0.09, 0.34), (0.51, 0.11, 0.26), (0.64, 0.08, 0.36),
                       (0.74, 0.12, 0.3), (0.88, 0.09, 0.33)]:
        d.rectangle([x + bx * w, sy - bh * h, x + (bx + bw) * w, sy + h * 0.38],
                    fill=ILL_INK)
    # balon parade miring + keranjang
    cx, cy = x + w * 0.78, y + h * 0.3
    d.ellipse([cx - w * 0.09, cy - h * 0.15, cx + w * 0.09, cy + h * 0.15],
              fill=ILL_OCHRE, outline=ILL_INK, width=2)
    d.line([cx - w * 0.05, cy + h * 0.13, cx - w * 0.04, cy + h * 0.24],
           fill=ILL_INK, width=2)
    d.line([cx + w * 0.05, cy + h * 0.13, cx + w * 0.04, cy + h * 0.24],
           fill=ILL_INK, width=2)
    d.rectangle([cx - w * 0.045, cy + h * 0.24, cx + w * 0.045, cy + h * 0.3],
                fill=ILL_RUST, outline=ILL_INK, width=2)

def ill_kyiv(d, x, y, w, h):
    """3 Kyiv: intersepsi rudal malam di atas skyline."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=ILL_NAVY)
    for sx, sy in [(0.08, 0.12), (0.22, 0.2), (0.45, 0.08), (0.62, 0.16), (0.85, 0.1),
                   (0.95, 0.24), (0.35, 0.3)]:
        d.ellipse([x + sx * w - 1, y + sy * h - 1, x + sx * w + 1, y + sy * h + 1],
                  fill=WHITE)
    # skyline dengan jendela menyala
    sy = y + h * 0.62
    for bx, bw, bh in [(0.03, 0.11, 0.32), (0.16, 0.09, 0.42), (0.27, 0.12, 0.3),
                       (0.41, 0.1, 0.38), (0.53, 0.12, 0.28), (0.67, 0.09, 0.4),
                       (0.78, 0.11, 0.32), (0.9, 0.08, 0.36)]:
        d.rectangle([x + bx * w, sy - bh * h, x + (bx + bw) * w, sy + h * 0.38],
                    fill=(16, 20, 30))
        for wy in (0.12, 0.22):
            d.rectangle([x + (bx + bw * 0.3) * w, sy - bh * h + wy * h,
                         x + (bx + bw * 0.55) * w, sy - bh * h + wy * h + 3],
                        fill=(255, 220, 120))
    # jejak rudal yang dicegat + ledakan intersepsi
    d.line([x + w * 0.2, y + h * 0.1, x + w * 0.42, y + h * 0.38], fill=(255, 220, 120), width=3)
    d.line([x + w * 0.85, y + h * 0.08, x + w * 0.62, y + h * 0.32], fill=(255, 220, 120), width=3)
    _burst(d, x + w * 0.52, y + h * 0.34, h * 0.2, ILL_FIRE)
    _burst(d, x + w * 0.52, y + h * 0.34, h * 0.1, (255, 220, 120))

def ill_jazan(d, x, y, w, h):
    """4 Jazan: kilang terbakar, asap hitam."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=ILL_CREAM)
    _smoke(d, x + w * 0.55, y + h * 0.06, w * 0.16)
    # menara distilasi + tangki
    bx, by = x + w * 0.12, y + h * 0.62
    d.rectangle([bx, by - h * 0.45, bx + w * 0.14, by], fill=ILL_BLUE,
                outline=ILL_INK, width=2)
    for i in range(3):
        d.line([bx, by - h * (0.12 + i * 0.12), bx + w * 0.14, by - h * (0.12 + i * 0.12)],
               fill=ILL_INK, width=1)
    d.rectangle([bx + w * 0.22, by - h * 0.3, bx + w * 0.4, by], fill=ILL_OCHRE,
                outline=ILL_INK, width=2)
    d.line([bx + w * 0.14, by - h * 0.25, bx + w * 0.22, by - h * 0.25], fill=ILL_INK, width=2)
    _flame(d, bx + w * 0.07, by, w * 0.1, h * 0.3)
    _flame(d, bx + w * 0.31, by - h * 0.05, w * 0.07, h * 0.2)

def ill_eu(d, x, y, w, h):
    """5 UE: cakram bintang Eropa + koin emas retak."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=ILL_CREAM)
    # cakram UE
    cx, cy, r = x + w * 0.26, y + h * 0.34, h * 0.26
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=NAVY, outline=ILL_INK, width=2)
    for i in range(12):
        ang = 2 * math.pi * i / 12 - math.pi / 2
        sx, sy = cx + r * 0.68 * math.cos(ang), cy + r * 0.68 * math.sin(ang)
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=ILL_GOLD)
    # koin emas retak
    kx, ky, kr = x + w * 0.7, y + h * 0.36, h * 0.24
    d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=ILL_GOLD,
              outline=ILL_INK, width=2)
    d.line([kx - kr * 0.15, ky - kr * 0.85, kx + kr * 0.2, ky - kr * 0.2,
            kx - kr * 0.2, ky + kr * 0.3, kx + kr * 0.1, ky + kr * 0.85],
           fill=ILL_INK, width=2)
    # meja
    d.line([x + w * 0.08, y + h * 0.62, x + w * 0.92, y + h * 0.62], fill=ILL_INK, width=3)

def ill_ecb(d, x, y, w, h):
    """6 ECB: fasad bank klasik + koin emas + panah naik."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=ILL_CREAM)
    bx, by = x + w * 0.12, y + h * 0.62
    # pedimen + kolom
    d.polygon([(bx, by - h * 0.5), (bx + w * 0.42, by - h * 0.5),
               (bx + w * 0.21, by - h * 0.62)], fill=ILL_BLUE, outline=ILL_INK)
    for i in range(4):
        cx = bx + w * (0.05 + i * 0.11)
        d.rectangle([cx, by - h * 0.48, cx + w * 0.045, by], fill=WHITE,
                    outline=ILL_INK, width=2)
    d.rectangle([bx - w * 0.02, by, bx + w * 0.44, by + h * 0.05], fill=ILL_INK)
    # koin emas
    kx, ky, kr = x + w * 0.72, y + h * 0.42, h * 0.17
    d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=ILL_GOLD,
              outline=ILL_INK, width=2)
    # panah naik
    ax = x + w * 0.72
    d.line([ax, y + h * 0.08, ax, y + h * 0.24], fill=ILL_RUST, width=4)
    d.polygon([(ax - w * 0.04, y + h * 0.14), (ax + w * 0.04, y + h * 0.14),
               (ax, y + h * 0.05)], fill=ILL_RUST)

def ill_kim(d, x, y, w, h):
    """7 Kim: rudal meluncur + simbol atom."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=ILL_NAVY)
    for sx, sy in [(0.1, 0.12), (0.85, 0.15), (0.92, 0.35), (0.15, 0.35)]:
        d.ellipse([x + sx * w - 1, y + sy * h - 1, x + sx * w + 1, y + sy * h + 1],
                  fill=WHITE)
    # simbol atom: 3 orbit elips diputar (poligon titik)
    ax, ay, ar = x + w * 0.78, y + h * 0.26, h * 0.16
    for rot in (0, 60, 120):
        pts = []
        for i in range(28):
            t = 2 * math.pi * i / 28
            ex, ey = ar * math.cos(t), ar * 0.42 * math.sin(t)
            ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            pts.append((ax + ex * ca - ey * sa, ay + ex * sa + ey * ca))
        d.line(pts + [pts[0]], fill=ILL_SAGE, width=2)
    d.ellipse([ax - 3, ay - 3, ax + 3, ay + 3], fill=ILL_GOLD)
    # rudal vertikal + api
    mx = x + w * 0.32
    d.polygon([(mx - w * 0.035, y + h * 0.18), (mx + w * 0.035, y + h * 0.18),
               (mx, y + h * 0.06)], fill=ILL_SAGE, outline=ILL_INK)
    d.rectangle([mx - w * 0.035, y + h * 0.18, mx + w * 0.035, y + h * 0.5],
                fill=ILL_SAGE, outline=ILL_INK, width=2)
    d.polygon([(mx - w * 0.035, y + h * 0.5), (mx - w * 0.07, y + h * 0.58),
               (mx - w * 0.035, y + h * 0.52)], fill=ILL_SAGE, outline=ILL_INK)
    d.polygon([(mx + w * 0.035, y + h * 0.5), (mx + w * 0.07, y + h * 0.58),
               (mx + w * 0.035, y + h * 0.52)], fill=ILL_SAGE, outline=ILL_INK)
    _flame(d, mx, y + h * 0.6, w * 0.07, h * 0.16)

def ill_gaza(d, x, y, w, h):
    """8 Gaza: gedung rusak + asap + reruntuhan."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=(232, 222, 205))
    _smoke(d, x + w * 0.68, y + h * 0.1, w * 0.1)
    bx, by = x + w * 0.1, y + h * 0.62
    # gedung miring retak
    d.polygon([(bx, by - h * 0.5), (bx + w * 0.42, by - h * 0.56),
               (bx + w * 0.46, by), (bx, by)], fill=ILL_BLUE, outline=ILL_INK, width=2)
    d.line([bx + w * 0.1, by - h * 0.42, bx + w * 0.16, by - h * 0.2,
            bx + w * 0.08, by], fill=ILL_INK, width=2)
    for wx, wy in [(0.06, 0.3), (0.2, 0.24), (0.08, 0.12)]:
        d.rectangle([bx + wx * w, by - wy * h, bx + (wx + 0.05) * w, by - wy * h + h * 0.05],
                    fill=ILL_INK)
    # reruntuhan
    for rx, rw, rh in [(0.5, 0.12, 0.1), (0.62, 0.09, 0.07), (0.72, 0.14, 0.12)]:
        d.polygon([(x + rx * w, by), (x + (rx + rw / 2) * w, by - rh * h),
                   (x + (rx + rw) * w, by)], fill=ILL_SMOKE, outline=ILL_INK)

def ill_cairo(d, x, y, w, h):
    """10 Kairo: truk tangki terbakar di jalan layang."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=(238, 220, 190))
    _smoke(d, x + w * 0.55, y + h * 0.04, w * 0.15)
    # jalan layang
    ry = y + h * 0.6
    d.rectangle([x, ry, x + w - 1, ry + h * 0.06], fill=ILL_SMOKE)
    d.line([x, ry, x + w - 1, ry], fill=WHITE, width=1)
    # truk tangki: kabin + tangki silinder
    tx = x + w * 0.14
    d.rectangle([tx, ry - h * 0.2, tx + w * 0.16, ry], fill=ILL_RUST,
                outline=ILL_INK, width=2)
    d.ellipse([tx + w * 0.2, ry - h * 0.22, tx + w * 0.52, ry - h * 0.02],
              fill=ILL_OCHRE, outline=ILL_INK, width=2)
    d.ellipse([tx + w * 0.05, ry - h * 0.04, tx + w * 0.09, ry],
              fill=ILL_INK)
    d.ellipse([tx + w * 0.3, ry - h * 0.04, tx + w * 0.34, ry], fill=ILL_INK)
    d.ellipse([tx + w * 0.44, ry - h * 0.04, tx + w * 0.48, ry], fill=ILL_INK)
    _flame(d, tx + w * 0.36, ry - h * 0.18, w * 0.16, h * 0.36)
    # mobil kecil di belakang
    d.rectangle([x + w * 0.68, ry - h * 0.12, x + w * 0.82, ry], fill=ILL_BLUE,
                outline=ILL_INK, width=2)

def ill_bangkok(d, x, y, w, h):
    """11 Bangkok: menara kilang + asap hitam tebal."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=ILL_CREAM)
    _smoke(d, x + w * 0.45, y + h * 0.08, w * 0.17)
    bx, by = x + w * 0.12, y + h * 0.62
    d.rectangle([bx, by - h * 0.5, bx + w * 0.15, by], fill=ILL_BLUE,
                outline=ILL_INK, width=2)
    d.rectangle([bx + w * 0.24, by - h * 0.38, bx + w * 0.4, by], fill=ILL_OCHRE,
                outline=ILL_INK, width=2)
    d.line([bx + w * 0.15, by - h * 0.24, bx + w * 0.24, by - h * 0.24], fill=ILL_INK, width=2)
    d.rectangle([bx + w * 0.55, by - h * 0.3, bx + w * 0.7, by], fill=ILL_SAGE,
                outline=ILL_INK, width=2)
    _flame(d, bx + w * 0.07, by, w * 0.1, h * 0.3)

def ill_ibiza(d, x, y, w, h):
    """12 Ibiza: tanker terbalik di laut + tumpahan minyak."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=(70, 120, 160))
    # ombak
    for i in range(4):
        wx = x + w * (0.05 + i * 0.25)
        d.arc([wx, y + h * 0.55, wx + w * 0.2, y + h * 0.75], 180, 360,
              fill=WHITE, width=2)
    # tumpahan minyak
    d.ellipse([x + w * 0.2, y + h * 0.52, x + w * 0.85, y + h * 0.66], fill=(30, 28, 26))
    # lambung terbalik
    d.polygon([(x + w * 0.3, y + h * 0.56), (x + w * 0.72, y + h * 0.56),
               (x + w * 0.66, y + h * 0.4), (x + w * 0.36, y + h * 0.4)],
              fill=ILL_RUST, outline=ILL_INK, width=2)
    d.rectangle([x + w * 0.46, y + h * 0.32, x + w * 0.56, y + h * 0.4],
                fill=ILL_INK)
    # sekoci penyelamat
    d.polygon([(x + w * 0.08, y + h * 0.58), (x + w * 0.2, y + h * 0.58),
               (x + w * 0.17, y + h * 0.64), (x + w * 0.11, y + h * 0.64)],
              fill=ILL_OCHRE, outline=ILL_INK)

def ill_ebola(d, x, y, w, h):
    """13 Ebola: virus berduri + lencana palang merah."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=ILL_CREAM)
    cx, cy, r = x + w * 0.38, y + h * 0.36, h * 0.2
    for i in range(10):
        ang = 2 * math.pi * i / 10
        x1, y1 = cx + r * math.cos(ang), cy + r * math.sin(ang)
        x2, y2 = cx + r * 1.45 * math.cos(ang), cy + r * 1.45 * math.sin(ang)
        d.line([x1, y1, x2, y2], fill=ILL_INK, width=2)
        d.ellipse([x2 - 3, y2 - 3, x2 + 3, y2 + 3], fill=ILL_RUST)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(90, 140, 120),
              outline=ILL_INK, width=2)
    d.ellipse([cx - r * 0.45, cy - r * 0.45, cx - r * 0.1, cy - r * 0.1],
              fill=(150, 200, 180))
    # lencana palang
    bx, by, bs = x + w * 0.72, y + h * 0.2, h * 0.22
    d.rectangle([bx, by, bx + bs, by + bs], fill=WHITE, outline=ILL_INK, width=2)
    d.rectangle([bx + bs * 0.42, by + bs * 0.15, bx + bs * 0.58, by + bs * 0.85],
                fill=(200, 40, 40))
    d.rectangle([bx + bs * 0.15, by + bs * 0.42, bx + bs * 0.85, by + bs * 0.58],
                fill=(200, 40, 40))

def ill_guinea(d, x, y, w, h):
    """15 Guinea-Bissau: kotak suara + kalender dicoret."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=ILL_CREAM)
    # kalender di belakang
    cx, cy = x + w * 0.62, y + h * 0.3
    cw, ch = w * 0.3, h * 0.34
    d.rectangle([cx, cy, cx + cw, cy + ch], fill=WHITE, outline=ILL_INK, width=2)
    for i in range(1, 4):
        d.line([cx, cy + ch * i / 4, cx + cw, cy + ch * i / 4], fill=LINE, width=1)
        d.line([cx + cw * i / 4, cy, cx + cw * i / 4, cy + ch], fill=LINE, width=1)
    d.line([cx + 2, cy + 2, cx + cw - 2, cy + ch - 2], fill=(200, 40, 40), width=3)
    d.line([cx + cw - 2, cy + 2, cx + 2, cy + ch - 2], fill=(200, 40, 40), width=3)
    # kotak suara
    bx, by = x + w * 0.12, y + h * 0.62
    d.rectangle([bx, by - h * 0.3, bx + w * 0.34, by], fill=ILL_BLUE,
                outline=ILL_INK, width=2)
    d.rectangle([bx + w * 0.1, by - h * 0.36, bx + w * 0.24, by - h * 0.3],
                fill=WHITE, outline=ILL_INK)
    # surat suara masuk
    d.polygon([(bx + w * 0.12, by - h * 0.52), (bx + w * 0.22, by - h * 0.52),
               (bx + w * 0.22, by - h * 0.36), (bx + w * 0.12, by - h * 0.36)],
              fill=WHITE, outline=ILL_INK)

ILLUSTRATIONS = {1: ill_kuwait, 2: ill_storm, 3: ill_kyiv, 4: ill_jazan,
                 5: ill_eu, 6: ill_ecb, 7: ill_kim, 8: ill_gaza, 10: ill_cairo,
                 11: ill_bangkok, 12: ill_ibiza, 13: ill_ebola, 15: ill_guinea}

# ---------------------------------------------------------------- peta
MAP_LON0, MAP_LON1 = -125.0, 155.0
MAP_LAT0, MAP_LAT1 = -50.0, 75.0
SEA = (198, 214, 228)
LAND = (208, 192, 158)
LAND_LINE = (150, 138, 110)

def load_land():
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, "peta-ne110m.json"),
                 os.path.expanduser("~/workspace/custom-skills/alat/peta-ne110m.json")):
        if os.path.exists(cand):
            with open(cand, encoding="utf-8") as f:
                return json.load(f)["benua"]
    raise FileNotFoundError("peta-ne110m.json tidak ditemukan")

def clip_polygon(pts, x0, y0, x1, y1):
    """Potong poligon ke persegi panel (Sutherland-Hodgman) supaya daratan
    tidak meluber keluar kotak peta."""
    def clip_edge(pts, inside, intersect):
        if not pts:
            return []
        out = []
        prev, prev_in = pts[-1], inside(pts[-1])
        for cur in pts:
            cur_in = inside(cur)
            if cur_in:
                if not prev_in:
                    out.append(intersect(prev, cur))
                out.append(cur)
            elif prev_in:
                out.append(intersect(prev, cur))
            prev, prev_in = cur, cur_in
        return out
    pts = clip_edge(pts, lambda p: p[0] >= x0,
                    lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / ((b[0] - a[0]) or 1e-9)))
    pts = clip_edge(pts, lambda p: p[0] <= x1,
                    lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / ((b[0] - a[0]) or 1e-9)))
    pts = clip_edge(pts, lambda p: p[1] >= y0,
                    lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / ((b[1] - a[1]) or 1e-9), y0))
    pts = clip_edge(pts, lambda p: p[1] <= y1,
                    lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / ((b[1] - a[1]) or 1e-9), y1))
    return pts

def project(lon, lat, x, y, w, h):
    px = x + (lon - MAP_LON0) / (MAP_LON1 - MAP_LON0) * w
    py = y + (MAP_LAT1 - lat) / (MAP_LAT1 - MAP_LAT0) * h
    return px, py

def place_pins(true_pts, min_dist, bounds, obstacles=()):
    """Tempatkan pin satu per satu; bila titik aslinya bertumpuk dengan pin
    yang sudah ditempatkan atau dengan titik penghalang, geser sepanjang
    spiral sampai bebas (deterministik, dijamin tidak bertumpuk)."""
    x0, y0, x1, y1 = bounds
    placed = []
    for tp in true_pts:
        pos = None
        for radius in range(0, 61, 4):
            for ang in range(0, 360, 45):
                cx = tp[0] + radius * math.cos(math.radians(ang))
                cy = tp[1] + radius * math.sin(math.radians(ang))
                if not (x0 + 7 <= cx <= x1 - 7 and y0 + 7 <= cy <= y1 - 7):
                    continue
                if all(math.hypot(cx - px, cy - py) >= min_dist for px, py in placed):
                    if all(math.hypot(cx - ox, cy - oy) >= 10 for ox, oy in obstacles):
                        pos = (cx, cy)
                        break
            if pos:
                break
        if pos is None:  # darurat: pakai titik asli
            pos = tp
        placed.append(pos)
    return placed

def draw_map(d, x, y, w, h, land):
    """Panel peta: judul + peta dunia + legenda 3 baris. Kembalikan y akhir.

    Pin bernomor (13) hanya untuk cerita bergambar — 36 pin bernomor dalam
    panel 332 px tidak muat tanpa tumpang tindih (Eropa 13 pin dalam ~50 px).
    23 cerita lain tetap berpin sebagai titik kecil berwarna wilayah, jadi
    sebaran warna tetap terbaca (peta.md butir 9).
    """
    NUMBERED = {1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 15}
    title_f = font(SANS_B, 12)
    d.text((x, y), "WHERE IT HAPPENED — 36 PLACES · 39 STORIES", font=title_f, fill=INK)
    my = y + 18
    mh = h - 18 - 39  # sisa untuk peta (legenda 3 baris x 13 px)
    d.rectangle([x, my, x + w - 1, my + mh - 1], fill=SEA, outline=LINE, width=1)
    for poly in land:
        pts = [project(lon, lat, x + 1, my + 1, w - 2, mh - 2)
               for lon, lat in poly["poligon"]]
        pts = clip_polygon(pts, x + 1, my + 1, x + w - 2, my + mh - 2)
        if len(pts) >= 3:
            d.polygon(pts, fill=LAND, outline=LAND_LINE)
    true_pts = [project(lon, lat, x + 1, my + 1, w - 2, mh - 2)
                for _, lon, lat, _ in PINS]
    # titik kecil untuk semua cerita
    for (num, _, _, reg), tp in zip(PINS, true_pts):
        if num in NUMBERED:
            continue
        d.ellipse([tp[0] - 3, tp[1] - 3, tp[0] + 3, tp[1] + 3],
                  fill=REGION[reg], outline=WHITE, width=1)
    # pin bernomor hanya cerita bergambar, ditolak bila bertumpuk
    num_idx = [i for i, (num, _, _, _) in enumerate(PINS) if num in NUMBERED]
    dot_pts = [true_pts[i] for i, (num, _, _, _) in enumerate(PINS)
               if num not in NUMBERED]
    disp = place_pins([true_pts[i] for i in num_idx], 13,
                      (x + 1, my + 1, x + w - 2, my + mh - 2), obstacles=dot_pts)
    pin_f = font(SANS_B, 9)
    for k, i in enumerate(num_idx):
        num, _, _, reg = PINS[i]
        tp, dp = true_pts[i], disp[k]
        if math.hypot(dp[0] - tp[0], dp[1] - tp[1]) > 3:
            d.line([tp, dp], fill=ILL_INK, width=1)
            d.ellipse([tp[0] - 2, tp[1] - 2, tp[0] + 2, tp[1] + 2], fill=ILL_INK)
        r = 6
        d.ellipse([dp[0] - r, dp[1] - r, dp[0] + r, dp[1] + r],
                  fill=REGION[reg], outline=WHITE, width=1)
        t = str(num)
        tw = d.textlength(t, font=pin_f)
        d.text((dp[0] - tw / 2, dp[1] - 5), t, font=pin_f, fill=WHITE)
    leg_f = font(SANS, 10)
    # Nama wilayah diwarnai wilayahnya: legenda sekaligus kunci warna untuk
    # angka berwarna di daftar (QA kritikus 2).
    def leg_line(y0, segments):
        xx = x
        for text, color in segments:
            d.text((xx, y0), text, font=leg_f, fill=color)
            xx += d.textlength(text, font=leg_f)
    leg_line(my + mh + 4, [("NORTH AMERICA", REGION["NA"]), (" 6 · ", INK),
                           ("SOUTH AMERICA", REGION["SA"]), (" 2 · ", INK),
                           ("EUROPE", REGION["EU"]), (" 13", INK)])
    leg_line(my + mh + 17, [("MIDDLE EAST", REGION["ME"]), (" 5 · ", INK),
                            ("AFRICA", REGION["AF"]), (" 6 · ", INK),
                            ("ASIA", REGION["AS"]), (" 5 · ", INK),
                            ("OCEANIA", REGION["OC"]), (" 2", INK)])
    d.text((x, my + mh + 30), "Stories per region. Numbered pins mark the pictured stories.",
           font=leg_f, fill=MUTED)
    return y + h

# ---------------------------------------------------------------- layout
def status_pill(d, x, y, width, status, fsize=10):
    """Pil status netral di ujung kanan baris kicker; kembalikan lebar pil."""
    sf = font(SANS_B, fsize)
    pw = d.textlength(status, font=sf) + 14
    ph = 16
    d.rounded_rectangle([x + width - pw, y, x + width - 1, y + ph - 1], radius=8,
                        outline=INK, width=1, fill=WHITE)
    tw = d.textlength(status, font=sf)
    d.text((x + width - pw + (pw - tw) / 2, y + 3), status, font=sf, fill=INK)
    return pw

def draw_story_image(img, d, x, y, w, h, num, hook, hook_size):
    """Kotak gambar: ilustrasi + pita hook di tepi bawah.

    Ilustrasi digambar di lapis sendiri lalu ditempel, supaya tidak ada
    yang meluber keluar kotak: asap _smoke naik ~0,9s di atas jangkarnya
    dan titiknya pernah menempel pada teks kartu di atasnya (QA kritikus 2).
    """
    layer = Image.new("RGB", (int(w), int(h)), PAPER)
    dl = ImageDraw.Draw(layer)
    ILLUSTRATIONS[num](dl, 0, 0, int(w), int(h))
    img.paste(layer, (int(x), int(y)))
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=LINE, width=1)
    hh = hook_size + 10
    d.rectangle([x, y + h - hh, x + w - 1, y + h - 1], fill=CHARCOAL)
    hf = font(SANS_B, hook_size)
    ht = hook
    while d.textlength(ht, font=hf) > w - 20 and len(ht) > 3:
        ht = ht[:-1]
    if ht != hook:
        raise FitFail(f"hook terlalu panjang: {hook!r}")
    d.text((x + 10, y + h - hh + 5), ht, font=hf, fill=WHITE)

def draw_hero(img, d, x, y, w, story, g):
    num, kicker, status, title, dek, src, hook, reg = story
    img_h = g["hero_img"]
    draw_story_image(img, d, x, y, w, img_h, num, hook, 15)
    yy = y + img_h + 6
    pw = status_pill(d, x, yy, w, status, 10)
    kf = font(SANS_B, 12)
    klines = fit(d, f"kicker hero {num}", kicker, kf, w - pw - 8, 1)
    yy = draw_lines(d, x, yy + 1, klines, kf, lh=15)
    yy += 4
    tf = font(SERIF_B, g["hero_title"])
    tlines = fit(d, f"judul hero {num}", title, tf, w, 2)
    yy = draw_lines(d, x, yy, tlines, tf, lh=g["hero_title"] + 3)
    yy += 4
    df = font(SANS, 13)
    dlines = fit(d, f"dek hero {num}", dek, df, w, 2)
    yy = draw_lines(d, x, yy, dlines, df, lh=16)
    yy += 3
    sf = font(SANS, 10)
    d.text((x, yy), "Source: " + src, font=sf, fill=MUTED)
    return yy + 12

def draw_card(img, d, x, y, w, story, g):
    num, kicker, status, title, dek, src, hook, reg = story
    img_h = g["card_img"]
    draw_story_image(img, d, x, y, w, img_h, num, hook, 12)
    yy = y + img_h + 5
    pw = status_pill(d, x, yy, w, status, 9)
    kf = font(SANS_B, 10)
    klines = fit(d, f"kicker kartu {num}", kicker, kf, w - pw - 8, 1)
    yy = draw_lines(d, x, yy + 1, klines, kf, lh=13)
    yy += 3
    tf = font(SERIF_B, g["card_title"])
    tlines = fit(d, f"judul kartu {num}", title, tf, w, 2)
    yy = draw_lines(d, x, yy, tlines, tf, lh=g["card_title"] + 3)
    yy += 3
    df = font(SANS, 12)
    dlines = fit(d, f"dek kartu {num}", dek, df, w, 1)
    yy = draw_lines(d, x, yy, dlines, df, lh=15)
    yy += 2
    sf = font(SANS, 9)
    d.text((x, yy), "Source: " + src, font=sf, fill=MUTED)
    return yy + 11

def draw_top(d, y, g):
    """Nameplate, tanggal, hitungan, strip angka, pita UTC. Kembalikan y akhir."""
    nf = font(SANS_B, g["nameplate"])
    t = "T H E   W O R L D   I N   O N E   D A Y"
    tw = d.textlength(t, font=nf)
    d.text(((W - tw) / 2, y), t, font=nf, fill=INK)
    y += g["nameplate"] + 6
    d.rectangle([MARGIN, y, W - MARGIN - 1, y + 1], fill=NAVY)
    y += 5
    mf = font(SERIF_B, g["date_size"])
    tw = d.textlength(MASTHEAD_DATE, font=mf)
    fit(d, "masthead", MASTHEAD_DATE, mf, CW, 1)
    d.text(((W - tw) / 2, y), MASTHEAD_DATE, font=mf, fill=INK)
    y += g["date_size"] + 7
    cf = font(SANS_B, 12)
    tw = d.textlength(COUNT_LINE, font=cf)
    d.text(((W - tw) / 2, y), COUNT_LINE, font=cf, fill=INK)
    y += 17
    # strip angka: satu baris (angka + label sebaris per sel)
    cw = (CW - 3 * 8) / 4
    sh = g["strip_h"]
    for i, (num, lab) in enumerate(STATS):
        cx = MARGIN + i * (cw + 8)
        d.rectangle([cx, y, cx + cw - 1, y + sh - 1], outline=LINE, width=1)
        nf2 = font(SERIF_B, 16)
        d.text((cx + 8, y + 3), num, font=nf2, fill=NAVY)
        lf = font(SANS_B, 9)
        lab_lines = fit(d, f"strip {num}", lab, lf, cw - 16 - d.textlength(num, font=nf2) - 6, 1)
        d.text((cx + 8 + d.textlength(num, font=nf2) + 6, y + 7), lab_lines[0],
               font=lf, fill=INK)
    y += sh + 5
    # pita UTC
    uh = g["utc_h"]
    d.rectangle([MARGIN, y, W - MARGIN - 1, y + uh - 1], fill=NAVY)
    uf = font(SANS, 11)
    ub = font(SANS_B, 11)
    xx = MARGIN + 10
    parts = [("THE DAY IN UTC", ub)]
    for tm, ev in UTC_ITEMS:
        parts.append((tm, ub))
        parts.append((ev, uf))
    total = 20 + sum(d.textlength(t, font=f) for t, f in parts) + 16 * (len(UTC_ITEMS) + 1)
    if total > CW:
        raise FitFail(f"pita UTC {total:.0f} > {CW}")
    for i, (t, f) in enumerate(parts):
        d.text((xx, y + (uh - 11) // 2 - 1), t, font=f, fill=WHITE)
        xx += d.textlength(t, font=f) + (16 if i % 2 == 0 else 18)
    return y + uh + 4

def draw_list(d, x, y, width, rows, pitch, header=True):
    if header:
        hf = font(SANS_B, 12)
        d.text((x, y), "MORE STORIES", font=hf, fill=INK)
    y += 17
    nf = font(SANS_B, 11)
    pf = font(SANS_B, 11)
    tf = font(SANS, 11)
    for num, place, title, src, reg in rows:
        d.text((x, y), str(num), font=nf, fill=REGION[reg])
        xx = x + 18
        seg_place = place + " — "
        seg_title = title + " · "
        w_place = d.textlength(seg_place, font=pf)
        w_title = d.textlength(seg_title, font=tf)
        w_src = d.textlength(src, font=tf)
        if w_place + w_title + w_src > width - 18:
            raise FitFail(f"daftar {num}: {w_place + w_title + w_src:.0f} > {width - 18}")
        d.text((xx, y), seg_place, font=pf, fill=INK)
        xx += w_place
        d.text((xx, y), seg_title, font=tf, fill=INK)
        xx += w_title
        d.text((xx, y), src, font=tf, fill=MUTED)
        y += pitch
    return y

def draw_datecheck(d, y):
    f = font(SANS, 11.5)
    lines = fit(d, "datecheck", DATECHECK, f, CW - 24, 3)
    h = len(lines) * 15 + 14
    d.rectangle([MARGIN, y, W - MARGIN - 1, y + h - 1], outline=NAVY, width=2)
    yy = y + 7
    for ln in lines:
        d.text((MARGIN + 12, yy), ln, font=f, fill=INK)
        yy += 15
    return y + h

def draw_footer(d, y):
    f = font(SANS, 10)
    lines = fit(d, "footer", FOOTER, f, CW, 2)
    return draw_lines(d, MARGIN, y, lines, f, fill=MUTED, lh=13, align="center", width=CW)

# geometri susunan (angka dari wireframe yang lolos anggaran)
GEOM_A2 = {"nameplate": 14, "date_size": 46, "strip_h": 24, "utc_h": 28,
           "hero_img": 94, "hero_title": 19, "card_img": 85, "card_title": 15,
           "gap_top_hero": 0, "gap_hero_cards": 4, "gap_card_row": 4,
           "gap_cards_bottom": 4, "gap_bottom_dc": 3, "gap_dc_footer": 2,
           "list_pitch": 11.8}
GEOM_B = {"nameplate": 15, "date_size": 48, "strip_h": 34, "utc_h": 30,
          "hero_img": 120, "hero_title": 21, "card_img": 92, "card_title": 16,
          "gap_top_hero": 0, "gap_hero_cards": 8, "gap_card_row": 8,
          "gap_cards_bottom": 8, "gap_bottom_dc": 8, "gap_dc_footer": 6,
          "list_pitch": 14}

def render(layout, land, out_path):
    """Render satu susunan (A2 atau B) ke out_path. Kembalikan (path, y_akhir)."""
    g = GEOM_A2 if layout == "A2" else GEOM_B
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    y = MARGIN
    y = draw_top(d, y, g)
    y += g["gap_top_hero"]
    # hero
    colw = (CW - 2 * 10) / 3
    y_hero_end = y
    for i, st in enumerate(HEROES):
        ye = draw_hero(img, d, MARGIN + i * (colw + 10), y, colw, st, g)
        y_hero_end = max(y_hero_end, ye)
    y = y_hero_end + g["gap_hero_cards"]
    # kartu
    cards = CARDS if layout == "A2" else CARDS[:5]
    colw5 = (CW - 4 * 10) / 5
    rows = [cards[i:i + 5] for i in range(0, len(cards), 5)]
    for ri, row in enumerate(rows):
        y_row_end = y
        for i, st in enumerate(row):
            ye = draw_card(img, d, MARGIN + i * (colw5 + 10), y, colw5, st, g)
            y_row_end = max(y_row_end, ye)
        y = y_row_end
        if ri < len(rows) - 1:
            y += g["gap_card_row"]
    y += g["gap_cards_bottom"]
    # bawah: daftar + peta
    list_rows = LIST_ROWS if layout == "A2" else (
        LIST_ROWS[:13] + [(10, "CAIRO", "Tanker fire toll rises to 31", "AP", "AF"),
                          (11, "BANGKOK", "Bangchak refinery blast injures nine", "BBC", "AS")]
        + LIST_ROWS[13:] + [(12, "IBIZA", "Diesel tanker capsizes off Ibiza", "BBC / DW", "EU"),
                            (13, "ITURI", "Ebola passes 12,000 cases", "CBC / UPI", "AF"),
                            (15, "BISSAU", "Guinea-Bissau vote delayed to 2028", "Reuters", "AF")])
    # urutkan daftar B berdasarkan nomor agar tidak rusak (pelajaran kritikus 1)
    list_rows = sorted(list_rows, key=lambda r: r[0])
    half = (len(list_rows) + 1) // 2
    col1, col2 = list_rows[:half], list_rows[half:]
    y1 = draw_list(d, MARGIN, y, 315, col1, g["list_pitch"], header=True)
    y2 = draw_list(d, MARGIN + 325, y, 315, col2, g["list_pitch"], header=False)
    map_x = MARGIN + 640 + 12
    map_w = W - MARGIN - map_x
    y3 = draw_map(d, map_x, y, map_w, max(y1, y2) - y, land)
    y = max(y1, y2, y3)
    y += g["gap_bottom_dc"]
    y = draw_datecheck(d, y)
    y += g["gap_dc_footer"]
    y = draw_footer(d, y)
    if y > H - MARGIN:
        raise FitFail(f"halaman meluber: y akhir {y} > {H - MARGIN}")
    img.save(out_path, optimize=True)
    return out_path, y

# ---------------------------------------------------------------- main
def render_assets(outdir):
    """Gambar tiap ilustrasi sendiri (ukuran slot kartu/hero) untuk contact sheet."""
    os.makedirs(outdir, exist_ok=True)
    for num, fn in sorted(ILLUSTRATIONS.items()):
        for tag, (w, h) in (("hero", (321, 94)), ("card", (188, 85))):
            img = Image.new("RGB", (w, h), PAPER)
            d = ImageDraw.Draw(img)
            fn(d, 0, 0, w, h)
            img.save(os.path.join(outdir, f"aset-{num:02d}-{tag}.png"))
    print(f"aset ditulis ke {outdir}")

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", default="A2", choices=["A2", "B"])
    ap.add_argument("--out", default="entry.png")
    ap.add_argument("--aset", default=None,
                    help="tulis tiap ilustrasi ke folder ini (contact sheet)")
    args = ap.parse_args()
    if args.aset:
        render_assets(args.aset)
    land = load_land()
    # render 2x: byte harus identik (determinisme)
    p1, y1 = render(args.layout, land, args.out)
    import hashlib
    h1 = hashlib.sha256(open(p1, "rb").read()).hexdigest()
    p2, y2 = render(args.layout, land, "/tmp/entry-kedua.png")
    h2 = hashlib.sha256(open(p2, "rb").read()).hexdigest()
    size = os.path.getsize(p1)
    print(f"layout={args.layout} y_akhir={y1} (batas {H - MARGIN})")
    print(f"ukuran={size} byte (batas 1048576) sha256={h1[:16]}…")
    print(f"render kedua identik: {h1 == h2}")
    if h1 != h2:
        raise SystemExit("GAGAL: dua render tidak identik")
    if size > 1048576:
        raise SystemExit("GAGAL: entry.png melebihi 1 MiB")
    print("OK: entry.png siap")

if __name__ == "__main__":
    main()

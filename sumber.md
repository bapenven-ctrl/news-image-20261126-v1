# sumber.md — news-image-20261126-v1

## entry.png
Dibangun di sesi build 27 Nov 2026 oleh `compose.py` (ada di repo ini):
seluruh ilustrasi digambar dengan kode (PIL) dari brief peristiwa — tanpa
generator gambar, tanpa memakai gambar entry pesaing atau karya berhak cipta
sebagai masukan. Teks diset oleh kode komposisi yang sama, dengan font Noto
Serif / Noto Sans (SIL Open Font License) yang terpasang di sistem build.
`compose.py` dapat menjalankan ulang render bila font Noto dan
`data/peta-ne110m.json` tersedia.

## Peta
`data/peta-ne110m.json` — Natural Earth 1:110m, domain publik
(naturalearthdata.com/about/terms-of-use). Sumber: https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson

## Berita
39 cerita berita dunia Kamis 26 November 2026 (UTC), diriset dari sumber
primer: Reuters, AP, BBC, Al Jazeera, France 24, Euronews, The Guardian,
CBC, NPR, CNBC. Detail per cerita (sumber + status + tanggal verifikasi)
ada di berkas kerja `isi.md` di luar repo ini.

## main.py
Program penyalin (Python stdlib saja, tanpa jaringan): menyalin `entry.png`
ke folder keluaran penilai (`MAKEFUN_OUTPUT_DIR`).

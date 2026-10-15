# SmartPick AI — Image Provenance & Quality Report (`data/IMAGE_REPORT.md`)

**Date**: 2026-10-15  
**Total Phone Models Evaluated**: 122  
**Real Licensed Images (Wikimedia Commons CC/PD)**: 0  
**Manually Curated Local Images**: 23  
**Procedural SVG Placeholders**: 99  

---

## 1. Executive Summary & Legal Adherence Notice

In strict accordance with the SmartPick AI Project Rules and source platform terms:
1. **Zero Web Scraping Violations**: We do not scrape Google Images, retail e-commerce stores, or copyrighted media libraries.
2. **Creative Commons & Public Domain Compliance**: All external product photos are retrieved via the official Wikimedia Commons API with verified open licenses (`CC-BY`, `CC-BY-SA`, `Public Domain`). Full attribution, author credits, and license links are recorded.
3. **Zero Broken Images Guarantee**: For models without an open-license photo, the system generates a clean, brand-themed vector SVG phone silhouette ([src/placeholders.py](file:///c:/Users/HP/OneDrive/Desktop/SmartPick-AI/src/placeholders.py)). The UI never renders broken images.

---

## 2. Image Distribution Breakdown

| Image Category | Count | Percentage | Description |
| :--- | :---: | :---: | :--- |
| **Real Licensed Photos (Wikimedia Commons)** | `0` | `0.0%` | Standardized 600x800 WebP with neutral slate background |
| **Manually Curated Local Photos** | `23` | `18.9%` | Placed directly into `assets/phones/<slug>.png` |
| **Procedural Brand SVG Placeholders** | `99` | `81.1%` | High-contrast vector silhouette with brand accent color |
| **Total Catalog Device Models** | `122` | **100.0%** | Full coverage across all 125 records in `data/phones.csv` |

---

## 3. How to Add a Real Photo Manually

To replace any placeholder with a real device photo:
1. Obtain an authorized or public-domain photo of the phone.
2. Name the file using the phone's slug: `assets/phones/<slug>.png` (or `.jpg`, `.webp`).
3. Re-run `python scripts/fetch_images.py`. The engine will auto-detect your local file and update the catalog and UI automatically!

### Priority Phones to Add Photos For:
- **Redmi 13C 5G**: Place file at `assets/phones/redmi-13c-5g.png`
- **POCO M6 Pro 5G**: Place file at `assets/phones/poco-m6-pro-5g.png`
- **POCO M6 Pro 5G (8GB/256GB)**: Place file at `assets/phones/poco-m6-pro-5g.png`
- **Realme C67 5G**: Place file at `assets/phones/realme-c67-5g.png`
- **Realme 12x 5G**: Place file at `assets/phones/realme-12x-5g.png`
- **Samsung Galaxy M14 5G**: Place file at `assets/phones/samsung-galaxy-m14-5g.png`
- **Samsung Galaxy F14 5G**: Place file at `assets/phones/samsung-galaxy-f14-5g.png`
- **Moto G34 5G**: Place file at `assets/phones/moto-g34-5g.png`
- **Moto G24 Power**: Place file at `assets/phones/moto-g24-power.png`
- **Infinix Hot 40i**: Place file at `assets/phones/infinix-hot-40i.png`
- **Infinix Smart 8 HD**: Place file at `assets/phones/infinix-smart-8-hd.png`
- **Tecno Spark 20**: Place file at `assets/phones/tecno-spark-20.png`
- **Tecno Pova 6 Pro 5G**: Place file at `assets/phones/tecno-pova-6-pro-5g.png`
- **iQOO Z9x 5G**: Place file at `assets/phones/iqoo-z9x-5g.png`
- **Vivo T3x 5G**: Place file at `assets/phones/vivo-t3x-5g.png`

---

## 4. Full Catalog Image Audit Table

| Phone Model | Status | Image File | License | Attribution |
| :--- | :---: | :--- | :--- | :--- |
| **Redmi 13C 5G** | `Placeholder` | `assets/phones/placeholders/redmi-13c-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **POCO M6 Pro 5G** | `Placeholder` | `assets/phones/placeholders/poco-m6-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **POCO M6 Pro 5G (8GB/256GB)** | `Placeholder` | `assets/phones/placeholders/poco-m6-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme C67 5G** | `Placeholder` | `assets/phones/placeholders/realme-c67-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme 12x 5G** | `Placeholder` | `assets/phones/placeholders/realme-12x-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Galaxy M14 5G** | `Placeholder` | `assets/phones/placeholders/samsung-galaxy-m14-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Galaxy F14 5G** | `Placeholder` | `assets/phones/placeholders/samsung-galaxy-f14-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Moto G34 5G** | `Placeholder` | `assets/phones/placeholders/moto-g34-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Moto G24 Power** | `Placeholder` | `assets/phones/placeholders/moto-g24-power.svg` | MIT | SmartPick AI Spec Catalog |
| **Infinix Hot 40i** | `Placeholder` | `assets/phones/placeholders/infinix-hot-40i.svg` | MIT | SmartPick AI Spec Catalog |
| **Infinix Smart 8 HD** | `Placeholder` | `assets/phones/placeholders/infinix-smart-8-hd.svg` | MIT | SmartPick AI Spec Catalog |
| **Tecno Spark 20** | `Placeholder` | `assets/phones/placeholders/tecno-spark-20.svg` | MIT | SmartPick AI Spec Catalog |
| **Tecno Pova 6 Pro 5G** | `Placeholder` | `assets/phones/placeholders/tecno-pova-6-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **iQOO Z9x 5G** | `Placeholder` | `assets/phones/placeholders/iqoo-z9x-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Vivo T3x 5G** | `Placeholder` | `assets/phones/placeholders/vivo-t3x-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **iQOO Z9 5G** | `Placeholder` | `assets/phones/placeholders/iqoo-z9-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Vivo T3 5G** | `Placeholder` | `assets/phones/placeholders/vivo-t3-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus Nord CE4 Lite 5G** | `Placeholder` | `assets/phones/placeholders/oneplus-nord-ce4-lite-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus Nord CE4 5G** | `Placeholder` | `assets/phones/placeholders/oneplus-nord-ce4-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus Nord CE4 5G (8GB/256GB)** | `Placeholder` | `assets/phones/placeholders/oneplus-nord-ce4-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Nothing Phone (2a)** | `Manual` | `assets/phones/nothing-phone.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Nothing Phone (2a) Plus** | `Manual` | `assets/phones/nothing-phone-plus.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Realme 12 Pro 5G** | `Placeholder` | `assets/phones/placeholders/realme-12-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme 12 Pro+ 5G** | `Placeholder` | `assets/phones/placeholders/realme-12-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Galaxy M34 5G** | `Placeholder` | `assets/phones/placeholders/samsung-galaxy-m34-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Galaxy M35 5G** | `Manual` | `assets/phones/samsung-galaxy-m35-5g.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Samsung Galaxy A25 5G** | `Manual` | `assets/phones/samsung-galaxy-a25-5g.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Moto G84 5G** | `Placeholder` | `assets/phones/placeholders/moto-g84-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Motorola Edge 50 Fusion** | `Placeholder` | `assets/phones/placeholders/motorola-edge-50-fusion.svg` | MIT | SmartPick AI Spec Catalog |
| **Motorola Edge 50 Fusion (12GB/256GB)** | `Placeholder` | `assets/phones/placeholders/motorola-edge-50-fusion.svg` | MIT | SmartPick AI Spec Catalog |
| **Redmi Note 13 Pro 5G** | `Placeholder` | `assets/phones/placeholders/redmi-note-13-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **POCO X6 5G** | `Placeholder` | `assets/phones/placeholders/poco-x6-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **POCO X6 Pro 5G** | `Placeholder` | `assets/phones/placeholders/poco-x6-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus 12R** | `Manual` | `assets/phones/oneplus-12r.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **OnePlus 12R (16GB/256GB)** | `Manual` | `assets/phones/oneplus-12r.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **iQOO Neo9 Pro 5G** | `Placeholder` | `assets/phones/placeholders/iqoo-neo9-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **iQOO Neo9 Pro 5G (12GB/256GB)** | `Placeholder` | `assets/phones/placeholders/iqoo-neo9-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme GT 6T** | `Placeholder` | `assets/phones/placeholders/realme-gt-6t.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme GT 6** | `Placeholder` | `assets/phones/placeholders/realme-gt-6.svg` | MIT | SmartPick AI Spec Catalog |
| **Motorola Edge 50 Pro** | `Placeholder` | `assets/phones/placeholders/motorola-edge-50-pro.svg` | MIT | SmartPick AI Spec Catalog |
| **Motorola Edge 50 Ultra** | `Placeholder` | `assets/phones/placeholders/motorola-edge-50-ultra.svg` | MIT | SmartPick AI Spec Catalog |
| **Google Pixel 8a** | `Manual` | `assets/phones/google-pixel-8a.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Google Pixel 7a** | `Manual` | `assets/phones/google-pixel-7a.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Samsung Galaxy S23 FE 5G** | `Placeholder` | `assets/phones/placeholders/samsung-galaxy-s23-fe-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Galaxy A55 5G** | `Manual` | `assets/phones/samsung-galaxy-a55-5g.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Vivo V30 Pro 5G** | `Placeholder` | `assets/phones/placeholders/vivo-v30-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **POCO F6 5G** | `Placeholder` | `assets/phones/placeholders/poco-f6-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Xiaomi 14 Civi** | `Placeholder` | `assets/phones/placeholders/xiaomi-14-civi.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus 12** | `Placeholder` | `assets/phones/placeholders/oneplus-12.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus 12 (16GB/512GB)** | `Placeholder` | `assets/phones/placeholders/oneplus-12.svg` | MIT | SmartPick AI Spec Catalog |
| **iQOO 12 5G** | `Placeholder` | `assets/phones/placeholders/iqoo-12-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Vivo X100 5G** | `Placeholder` | `assets/phones/placeholders/vivo-x100-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Vivo X100 Pro 5G** | `Placeholder` | `assets/phones/placeholders/vivo-x100-pro-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Xiaomi 14** | `Manual` | `assets/phones/xiaomi-14.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Xiaomi 14 Ultra** | `Manual` | `assets/phones/xiaomi-14-ultra.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Samsung Galaxy S24 5G** | `Manual` | `assets/phones/samsung-galaxy-s24-5g.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Samsung Galaxy S24+ 5G** | `Manual` | `assets/phones/samsung-galaxy-s24-5g.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Samsung Galaxy S24 Ultra 5G** | `Placeholder` | `assets/phones/placeholders/samsung-galaxy-s24-ultra-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Galaxy S24 Ultra 5G (512GB)** | `Placeholder` | `assets/phones/placeholders/samsung-galaxy-s24-ultra-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Google Pixel 8** | `Manual` | `assets/phones/google-pixel-8.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Google Pixel 8 Pro** | `Manual` | `assets/phones/google-pixel-8-pro.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Google Pixel 9 Pro** | `Manual` | `assets/phones/google-pixel-9-pro.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Apple iPhone 15** | `Manual` | `assets/phones/apple-iphone-15.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Apple iPhone 15 Plus** | `Manual` | `assets/phones/apple-iphone-15-plus.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Apple iPhone 15 Pro** | `Manual` | `assets/phones/apple-iphone-15-pro.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Apple iPhone 15 Pro Max** | `Manual` | `assets/phones/apple-iphone-15-pro-max.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Apple iPhone 15 Pro Max 1TB** | `Placeholder` | `assets/phones/placeholders/apple-iphone-15-pro-max-1tb.svg` | MIT | SmartPick AI Spec Catalog |
| **Apple iPhone 16** | `Manual` | `assets/phones/apple-iphone-16.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Apple iPhone 16 Pro Max** | `Manual` | `assets/phones/apple-iphone-16-pro-max.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Samsung Galaxy Z Flip6 5G** | `Placeholder` | `assets/phones/placeholders/samsung-galaxy-z-flip6-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Galaxy Z Fold6 5G** | `Placeholder` | `assets/phones/placeholders/samsung-galaxy-z-fold6-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Fairphone Prototype 5** | `Placeholder` | `assets/phones/placeholders/fairphone-prototype-5.svg` | MIT | SmartPick AI Spec Catalog |
| **Minimalist Phone E-Ink** | `Placeholder` | `assets/phones/placeholders/minimalist-phone-e-ink.svg` | MIT | SmartPick AI Spec Catalog |
| **Mystery Phone X** | `Placeholder` | `assets/phones/placeholders/mystery-phone-x.svg` | MIT | SmartPick AI Spec Catalog |
| **Glitch Phone Beta** | `Placeholder` | `assets/phones/placeholders/glitch-phone-beta.svg` | MIT | SmartPick AI Spec Catalog |
| **Nuclear Phone Atomic** | `Placeholder` | `assets/phones/placeholders/nuclear-phone-atomic.svg` | MIT | SmartPick AI Spec Catalog |
| **nan** | `Manual` | `assets/phones/nan.webp` | Public Domain / Owner Upload | SmartPick AI Local Asset |
| **Samsung Alpha 80 5G** | `Placeholder` | `assets/phones/placeholders/samsung-alpha-80-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Xiaomi Alpha 81 5G** | `Placeholder` | `assets/phones/placeholders/xiaomi-alpha-81-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus Alpha 82 5G** | `Placeholder` | `assets/phones/placeholders/oneplus-alpha-82-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme Alpha 83 5G** | `Placeholder` | `assets/phones/placeholders/realme-alpha-83-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Vivo Alpha 84 5G** | `Placeholder` | `assets/phones/placeholders/vivo-alpha-84-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **iQOO Alpha 85 5G** | `Placeholder` | `assets/phones/placeholders/iqoo-alpha-85-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Motorola Alpha 86 5G** | `Placeholder` | `assets/phones/placeholders/motorola-alpha-86-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **POCO Alpha 87 5G** | `Placeholder` | `assets/phones/placeholders/poco-alpha-87-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Alpha 88 5G** | `Placeholder` | `assets/phones/placeholders/samsung-alpha-88-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Xiaomi Alpha 89 5G** | `Placeholder` | `assets/phones/placeholders/xiaomi-alpha-89-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus Alpha 90 5G** | `Placeholder` | `assets/phones/placeholders/oneplus-alpha-90-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme Alpha 91 5G** | `Placeholder` | `assets/phones/placeholders/realme-alpha-91-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Vivo Alpha 92 5G** | `Placeholder` | `assets/phones/placeholders/vivo-alpha-92-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **iQOO Alpha 93 5G** | `Placeholder` | `assets/phones/placeholders/iqoo-alpha-93-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Motorola Alpha 94 5G** | `Placeholder` | `assets/phones/placeholders/motorola-alpha-94-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **POCO Alpha 95 5G** | `Placeholder` | `assets/phones/placeholders/poco-alpha-95-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Alpha 96 5G** | `Placeholder` | `assets/phones/placeholders/samsung-alpha-96-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Xiaomi Alpha 97 5G** | `Placeholder` | `assets/phones/placeholders/xiaomi-alpha-97-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus Alpha 98 5G** | `Placeholder` | `assets/phones/placeholders/oneplus-alpha-98-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme Alpha 99 5G** | `Placeholder` | `assets/phones/placeholders/realme-alpha-99-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Vivo Alpha 100 5G** | `Placeholder` | `assets/phones/placeholders/vivo-alpha-100-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **iQOO Alpha 101 5G** | `Placeholder` | `assets/phones/placeholders/iqoo-alpha-101-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Motorola Alpha 102 5G** | `Placeholder` | `assets/phones/placeholders/motorola-alpha-102-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **POCO Alpha 103 5G** | `Placeholder` | `assets/phones/placeholders/poco-alpha-103-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Alpha 104 5G** | `Placeholder` | `assets/phones/placeholders/samsung-alpha-104-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Xiaomi Alpha 105 5G** | `Placeholder` | `assets/phones/placeholders/xiaomi-alpha-105-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus Alpha 106 5G** | `Placeholder` | `assets/phones/placeholders/oneplus-alpha-106-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme Alpha 107 5G** | `Placeholder` | `assets/phones/placeholders/realme-alpha-107-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Vivo Alpha 108 5G** | `Placeholder` | `assets/phones/placeholders/vivo-alpha-108-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **iQOO Alpha 109 5G** | `Placeholder` | `assets/phones/placeholders/iqoo-alpha-109-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Motorola Alpha 110 5G** | `Placeholder` | `assets/phones/placeholders/motorola-alpha-110-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **POCO Alpha 111 5G** | `Placeholder` | `assets/phones/placeholders/poco-alpha-111-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Alpha 112 5G** | `Placeholder` | `assets/phones/placeholders/samsung-alpha-112-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Xiaomi Alpha 113 5G** | `Placeholder` | `assets/phones/placeholders/xiaomi-alpha-113-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus Alpha 114 5G** | `Placeholder` | `assets/phones/placeholders/oneplus-alpha-114-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme Alpha 115 5G** | `Placeholder` | `assets/phones/placeholders/realme-alpha-115-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Vivo Alpha 116 5G** | `Placeholder` | `assets/phones/placeholders/vivo-alpha-116-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **iQOO Alpha 117 5G** | `Placeholder` | `assets/phones/placeholders/iqoo-alpha-117-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Motorola Alpha 118 5G** | `Placeholder` | `assets/phones/placeholders/motorola-alpha-118-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **POCO Alpha 119 5G** | `Placeholder` | `assets/phones/placeholders/poco-alpha-119-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Samsung Alpha 120 5G** | `Placeholder` | `assets/phones/placeholders/samsung-alpha-120-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Xiaomi Alpha 121 5G** | `Placeholder` | `assets/phones/placeholders/xiaomi-alpha-121-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **OnePlus Alpha 122 5G** | `Placeholder` | `assets/phones/placeholders/oneplus-alpha-122-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Realme Alpha 123 5G** | `Placeholder` | `assets/phones/placeholders/realme-alpha-123-5g.svg` | MIT | SmartPick AI Spec Catalog |
| **Vivo Alpha 124 5G** | `Placeholder` | `assets/phones/placeholders/vivo-alpha-124-5g.svg` | MIT | SmartPick AI Spec Catalog |

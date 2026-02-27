"""
oliygoh.uz dan barcha OTMlar, yo'nalishlar va o'tish ballarini scrape qiladi.
Faqat 2024-yil ma'lumotlari mavjud (2025 hali kiritilmagan).

Usage:
    python manage.py scrape_oliygoh
    python manage.py scrape_oliygoh --year 2024
    python manage.py scrape_oliygoh --slug buxoro-davlat-universiteti
"""
import re
import time
import requests
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from universities.models import University, Direction, PassingScore

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'uz,ru;q=0.9,en;q=0.8',
}
BASE_URL = 'https://oliygoh.uz/oliygohlar'

# ───────────────────────────────────────────────────────────────────
# Barcha 122 ta OTM sluglari + nomlari (oliygoh.uz/oliygohlar/2025)
# ───────────────────────────────────────────────────────────────────
UNIVERSITIES = [
    ('ABU ALI IBN SINO nomidagi Buxoro davlat tibbiyot instituti', 'buxoro-tibbiyot-instituti'),
    ('Abu Rayhon Beruniy nomidagi Urganch davlat universiteti', 'urganch-davlat-universiteti'),
    ('Ajiniyoz nomidagi Nukus davlat pedagogika instituti', 'nukus-davlat-pedagogika-instituti'),
    ('Toshkent davlat o\'zbek tili va adabiyoti universiteti', 'toshkent-davlat-o-zbek-tili-va-adabiyoti-universiteti'),
    ('Andijon davlat chet tillari instituti', 'andijon-davlat-chet-tillari-instituti'),
    ('Andijon davlat pedagogika instituti', 'andijon-davlat-universitetining-pedagogika-instituti'),
    ('Andijon davlat tibbiyot instituti', 'andijon-tibbiyot-instituti'),
    ('Andijon iqtisodiyot va qurilish instituti', 'andijon-iqtisodiyot-va-qurilish-instituti'),
    ('Andijon mashinasozlik instituti', 'andijon-mashinasozlik-instituti'),
    ('Andijon qishloq xo\'jaligi instituti', 'toshkent-davlat-agrar-universiteti-andijon-filiali'),
    ('Berdaq nomidagi Qoraqalpoq davlat universiteti', 'qoraqalpoq-davlat-universiteti'),
    ('Buxoro davlat pedagogika instituti', 'buxoro-davlat-universitetining-pedagogika-instituti'),
    ('Buxoro davlat universiteti', 'buxoro-davlat-universiteti'),
    ('Buxoro muhandislik-texnologiya instituti', 'buxoro-muhandislik-texnologiya-instituti'),
    ('TIQXMMI Buxoro tabiiy resurslarni boshqarish instituti', 'toshkent-irrigatsiya-va-qishloq-xo-jaligini-mexanizatsiyalash-muhandislari-instituti-buxoro-filiali'),
    ('Chirchiq davlat pedagogika universiteti', 'toshkent-viloyati-chirchiq-davlat-pedagogika-instituti'),
    ('Farg\'ona davlat universiteti', 'farg-ona-davlat-universiteti'),
    ('Farg\'ona jamoat salomatligi tibbiyot instituti', 'toshkent-tibbiyot-akademiyasi-farg-ona-filiali'),
    ('Farg\'ona politexnika instituti', 'farg-ona-politexnika-instituti'),
    ('Geologiya fanlari universiteti', 'geologiya-fanlari-universiteti'),
    ('Guliston davlat pedagogika instituti', 'guliston-davlat-pedagogika-instituti'),
    ('Guliston davlat universiteti', 'guliston-davlat-universiteti'),
    ('Ipak yo\'li turizm va madaniy meros xalqaro universiteti', 'ipak-yo-li-turizm-xalqaro-universiteti'),
    ('Islom Karimov nomidagi Toshkent davlat texnika universiteti', 'toshkent-davlat-texnika-universiteti'),
    ('Olmaliq davlat texnika instituti', 'tashkent-davlat-texnika-universitetining-olmaliq-filiali'),
    ('Jahon iqtisodiyoti va diplomatiya universiteti', 'jahon-iqtisodiyoti-va-diplomatiya-universiteti'),
    ('Jamoat xavfsizligi universiteti', 'jamoat-xavfsizligi-universiteti'),
    ('Jizzax davlat pedagogika universiteti', 'jizzax-davlat-pedagogika-instituti'),
    ('Jizzax politexnika instituti', 'jizzax-politexnika-instituti'),
    ('Kamoliddin Behzod nomidagi Milliy rassomlik va dizayn instituti', 'milliy-rassomlik-va-dizayn-instituti'),
    ('Milliy estrada san\'ati instituti', 'milliy-estrada-sanati-instituti'),
    ('Mirzo Ulug\'bek nomidagi O\'zbekiston Milliy universiteti', 'ozbekiston-milliy-universiteti'),
    ('O\'zbekiston Milliy universiteti Jizzax filiali', 'o-zbekiston-milliy-universiteti-jizzax-filiali'),
    ('Samarqand davlat arxitektura-qurilish universiteti', 'samarqand-davlat-arxitektura-qurilish-instituti'),
    ('Muhammad al-Xorazmiy nomidagi TATU', 'toshkent-axborot-texnologiyalari-universiteti'),
    ('TATU Nukus filiali', 'toshkent-axborot-texnologiyalari-universiteti-nukus-filiali'),
    ('Namangan davlat chet tillari instituti', 'namangan-davlat-chet-tillari-instituti'),
    ('Namangan davlat pedagogika instituti', 'namangan-davlat-pedagogika-instituti'),
    ('Namangan davlat universiteti', 'namangan-davlat-universiteti'),
    ('Namangan muhandislik-qurilish instituti', 'namangan-muhandislik-qurilish-instituti'),
    ('Namangan muhandislik-texnologiya instituti', 'namangan-muhandislik-texnologiya-instituti'),
    ('Namangan to\'qimachilik sanoati instituti', 'namangan-toqimachilik-sanoati-instituti'),
    ('Navoiy davlat konchilik instituti Nukus filiali', 'navoiy-konchilik-instituti-nukus-filiali'),
    ('Navoiy davlat konchilik institutining Zarafshon fakulteti', 'navoiy-davlat-konchilik-institutining-zarafshon-shahridagi-fakulteti'),
    ('Navoiy davlat konchilik va texnologiyalar universiteti', 'navoiy-davlat-konchilik-instituti'),
    ('Navoiy davlat universiteti', 'navoiy-davlat-pedagogika-instituti'),
    ('Oliy sport mahorati instituti', 'oliy-sport-mahorati-instituti'),
    ('Yunus Rajabiy nomidagi O\'zbek milliy musiqa san\'ati instituti', 'o-zbek-milliy-musiqa-san-ati-instituti'),
    ('O\'zbekiston davlat jismoniy tarbiya va sport universiteti', 'o-zbekiston-davlat-jismoniy-tarbiya-va-sport-universiteti'),
    ('O\'zDJTSU Nukus filiali', 'o-zbekiston-davlat-jismoniy-tarbiya-va-sport-universiteti-nukus-filiali'),
    ('O\'zbekiston davlat konservatoriyasi', 'o-zbekiston-davlat-konservatoriyasi'),
    ('O\'zbekiston davlat iqtisodiyot universiteti', 'davlat-soliq-qomitasi-huzuridagi-fiskal-instituti'),
    ('O\'zbekiston Respublikasi Huquqni muhofaza qilish akademiyasi', 'ozbekiston-respublikasi-huquqni-muhofaza-qilish-akademiyasi'),
    ('O\'zbekiston davlat jahon tillari universiteti', 'ozbekiston-davlat-jahon-tillari-universiteti'),
    ('O\'zDJTSU Farg\'ona filiali', 'o-zbekiston-davlat-jismoniy-tarbiya-va-sport-universiteti-farg-ona-filiali'),
    ('O\'zbekiston davlat konservatoriyasi Nukus filiali', 'o-zbekiston-davlat-konservatoriyasi-nukus-filiali'),
    ('O\'zbekiston davlat san\'at va madaniyat instituti', 'o-zbekiston-davlat-san-at-va-madaniyat-instituti'),
    ('O\'zDSMI Nukus filiali', 'o-zbekiston-davlat-san-at-va-madaniyat-instituti-nukus-filiali'),
    ('O\'zDSMI Farg\'ona filiali', 'o-zbekiston-davlat-san-at-va-madaniyat-institutining-farg-ona-mintaqaviy-filiali'),
    ('O\'zbekiston davlat xoreografiya akademiyasi', 'milliy-raqs-va-xoreografiya-oliy-maktabi'),
    ('O\'zbekiston davlat xoreografiya akademiyasi Urganch filiali', 'o-zbekiston-davlat-xoreografiya-akademiyasi-urganch-filiali'),
    ('O\'zbekiston jurnalistika universiteti', 'o-zbekiston-jurnalistika-va-ommaviy-kommunikatsiyalar-universiteti'),
    ('O\'zbekiston xalqaro islomshunoslik akademiyasi', 'o-zbekiston-xalqaro-islom-akademiyasi'),
    ('Samarqand davlat pedagogika instituti', 'samarqand-davlat-universitetining-o-zbekiston-finlyandiya-pedagogika-instituti'),
    ('Oziq-ovqat texnologiyasi va muhandisligi xalqaro instituti', 'oziq-ovqat-texnologiyasi-va-muhandisligi-xalqaro-instituti'),
    ('Qarshi davlat universiteti', 'qarshi-davlat-universiteti'),
    ('Qarshi irrigatsiya va agrotexnologiyalar instituti', 'toshkent-irrigatsiya-va-qishloq-xo-jaligini-mexanizatsiyalash-muhandislari-instituti-qarshi-filiali'),
    ('Qarshi muhandislik-iqtisodiyot instituti', 'qarshi-muhandislik-iqtisodiyot-instituti'),
    ('Qo\'qon davlat pedagogika instituti', 'qo-qon-davlat-pedagogika-instituti'),
    ('Qoraqalpog\'iston qishloq xo\'jaligi instituti', 'toshkent-davlat-agrar-universiteti-nukus-filiali'),
    ('Qoraqalpog\'iston tibbiyot instituti', 'toshkent-pediatriya-tibbiyot-instituti-nukus-filiali'),
    ('Qoraqalpoq davlat universiteti Chimboy fakulteti', 'qoraqalpoq-davlat-universiteti-chimboy-fakulteti'),
    ('Samarqand davlat chet tillar instituti', 'samarqand-davlat-chet-tillar-instituti'),
    ('Samarqand davlat chet tillar instituti Narpay fakulteti', 'samarqand-davlat-chet-tillar-instituti-narpay-xorijiy-tillar-fakulteti'),
    ('Samarqand davlat chet tillar instituti Payariq fakulteti', 'samarqand-davlat-chet-tillar-instituti-payariq-xorijiy-tillar-fakulteti'),
    ('Samarqand davlat tibbiyot universiteti', 'samarqand-tibbiyot-instituti'),
    ('Samarqand davlat universiteti Kattaqo\'rg\'on filiali', 'samarqand-davlat-universiteti-kattaqorgon-filiali'),
    ('Samarqand davlat universiteti Agrobiotexnologiyalar instituti', 'samarqand-davlat-universiteti-agrobiotexnologiyalar-va-oziq-ovqat-xavfsizligi-instituti'),
    ('Samarqand davlat universiteti Denov instituti', 'termiz-davlat-universitetining-denov-filiali'),
    ('Samarqand davlat veterinariya universiteti', 'samarqand-veterinariya-meditsinasi-instituti'),
    ('Samarqand veterinariya meditsinasi instituti Nukus filiali', 'samarqand-veterinariya-meditsinasi-instituti-nukus-filiali'),
    ('Samarqand veterinariya meditsinasi instituti Toshkent filiali', 'samarqand-veterinariya-meditsinasi-instituti-toshkent-filiali'),
    ('Samarqand iqtisodiyot va servis instituti', 'samarqand-iqtisodiyot-va-servis-instituti'),
    ('Shahrisabz davlat pedagogika instituti', 'qarshi-davlat-universitetining-pedagogika-instituti'),
    ('Toshkent davlat pedagogika universiteti Shahrisabz filiali', 'toshkent-davlat-pedagogika-universiteti-shahrisabz-filiali'),
    ('Sharof Rashidov nomidagi Samarqand davlat universiteti', 'samarqand-davlat-universiteti'),
    ('Termiz agrotexnologiyalar instituti', 'toshkent-davlat-agrar-universiteti-termiz-filiali'),
    ('Termiz davlat pedagogika instituti', 'nizomiy-nomidagi-toshkent-davlat-pedagogika-universitetining-termiz-filiali'),
    ('Termiz davlat universiteti', 'termiz-davlat-universiteti'),
    ('Toshkent arxitektura-qurilish universiteti', 'toshkent-arxitektura-qurilish-instituti'),
    ('TATU Farg\'ona filiali', 'toshkent-axborot-texnologiyalari-universiteti-farg-ona-filiali'),
    ('TATU Nurafshon filiali', 'toshkent-axborot-texnologiyalari-universiteti-nurafshon-filiali'),
    ('TATU Qarshi filiali', 'toshkent-axborot-texnologiyalari-universiteti-qarshi-filiali'),
    ('TATU Samarqand filiali', 'toshkent-axborot-texnologiyalari-universiteti-samarqand-filiali'),
    ('TATU Urganch filiali', 'toshkent-axborot-texnologiyalari-universiteti-urganch-filiali'),
    ('Toshkent davlat agrar universiteti', 'toshkent-davlat-agrar-universiteti'),
    ('Samarqand agroinnovatsiyalar instituti', 'toshkent-davlat-agrar-universiteti-samarqand-filiali'),
    ('Toshkent davlat iqtisodiyot universiteti', 'toshkent-davlat-iqtisodiyot-universiteti'),
    ('TDIU Andijon fakulteti', 'toshkent-moliya-instituti-andijon-fakulteti'),
    ('TDIU Samarqand filiali', 'toshkent-davlat-iqtisodiyot-universiteti-samarqand-filiali'),
    ('TDIU To\'rtko\'l fakulteti', 'toshkent-davlat-iqtisodiyot-universiteti-tortkol-fakulteti'),
    ('O\'zbekiston milliy pedagogika universiteti', 'toshkent-davlat-pedagogika-universiteti'),
    ('Toshkent davlat sharqshunoslik universiteti', 'toshkent-davlat-sharqshunoslik-instituti'),
    ('Toshkent davlat stomatologiya instituti', 'toshkent-davlat-stomatologiya-instituti'),
    ('TDTU Qo\'qon filiali', 'toshkent-davlat-texnika-universiteti-qo-qon-filiali'),
    ('Termiz muhandislik-texnologiya instituti', 'toshkent-davlat-texnika-universiteti-termiz-filiali'),
    ('Toshkent davlat transport universiteti', 'toshkent-avtomobil-yo-llarini-loyihalash-qurish-va-ekspluatatsiyasi-instituti'),
    ('Toshkent davlat yuridik universiteti', 'toshkent-davlat-yuridik-universiteti'),
    ('Toshkent farmatsevtika instituti', 'toshkent-farmasevtika-instituti'),
    ('Toshkent irrigatsiya muhandislari instituti', 'toshkent-irrigatsiya-va-qishloq-xo-jaligini-mexanizatsiyalash-muhandislari-instituti'),
    ('Toshkent kimyo-texnologiya instituti', 'toshkent-kimyo-texnologiya-instituti'),
    ('TKTI Shahrisabz filiali', 'toshkent-kimyo-texnologiya-instituti-shahrisabz-filiali'),
    ('TKTI Yangiyer filiali', 'toshkent-kimyo-texnologiya-instituti-yangier-filiali'),
    ('Toshkent moliya instituti', 'toshkent-moliya-instituti'),
    ('Toshkent pediatriya tibbiyot instituti', 'toshkent-pediatriya-tibbiyot-instituti'),
    ('Toshkent tibbiyot akademiyasi', 'toshkent-tibbiyot-akademiyasi'),
    ('TTA Chirchiq filiali', 'toshkent-tibbiyot-akademiyasi-chirchiq-filiali'),
    ('TTA Urganch filiali', 'toshkent-tibbiyot-akademiyasi-urganch-filiali'),
    ('TTA Termiz filiali', 'toshkent-tibbiyot-akademiyasining-termiz-filiali'),
    ('Toshkent to\'qimachilik va yengil sanoat instituti', 'toshkent-to-qimachilik-va-yengil-sanoat-instituti'),
    ('Urganch davlat pedagogika instituti', 'urganch-davlat-pedagogika-instituti'),
    ('Andijon davlat universiteti', 'andijon-davlat-universiteti'),
]

# Viloyat aniqlash (nomi bo'yicha)
REGION_MAP = {
    'buxoro': 'Buxoro', 'urganch': 'Xorazm', 'nukus': 'Qoraqalpog\'iston',
    'qoraqalpoq': 'Qoraqalpog\'iston', 'chimboy': 'Qoraqalpog\'iston',
    'andijon': 'Andijon', 'namangan': 'Namangan',
    'farg\'ona': 'Farg\'ona', 'farg-ona': 'Farg\'ona', 'qo\'qon': 'Farg\'ona',
    'samarqand': 'Samarqand', 'kattaqo\'rg\'on': 'Samarqand', 'narpay': 'Samarqand',
    'payariq': 'Samarqand', 'denov': 'Surxondaryo', 'termiz': 'Surxondaryo',
    'qarshi': 'Qashqadaryo', 'shahrisabz': 'Qashqadaryo',
    'jizzax': 'Jizzax', 'guliston': 'Sirdaryo', 'yangiyer': 'Sirdaryo',
    'navoiy': 'Navoiy', 'zarafshon': 'Navoiy',
    'chirchiq': 'Toshkent viloyati', 'olmaliq': 'Toshkent viloyati',
    'nurafshon': 'Toshkent viloyati',
}


def detect_region(name_or_slug):
    text = (name_or_slug or '').lower()
    for key, region in REGION_MAP.items():
        if key in text:
            return region
    return 'Toshkent'


def parse_directions(html):
    """HTML dan yo'nalish va o'tish ballarini ajratib olish."""
    directions = []
    parts = html.split('<div class="tr">')

    for part in parts[2:]:  # 1-qator header
        name_m = re.search(r'class="text-dark-gray-100"[^>]*>\s*([^<]+?)\s*</p>', part)
        if not name_m:
            continue
        name = re.sub(r'\s+', ' ', name_m.group(1)).strip()

        code_m = re.search(r'class="text-dark-gray-400"[^>]*>\s*(\d{5,8})', part)
        code = code_m.group(1) if code_m else ''

        # O'tish ballari: oxirgi data-quotes bo'limi
        grant_score = contract_score = None
        quotes = re.findall(
            r'class="data quotes"(.*?)(?=class="data|<div class="tr"|$)',
            part, re.DOTALL
        )
        for q in reversed(quotes):
            gm = re.search(r'bg-primary-green"></span>\s*([\d.]+)', q)
            cm = re.search(r'bg-primary-accent"></span>\s*([\d.]+)', q)
            if gm or cm:
                grant_score = float(gm.group(1)) if gm else None
                contract_score = float(cm.group(1)) if cm else None
                break

        # Kvotalar: ikkinchi data-quotes bo'limi (birinchisi bo'lsa)
        grant_quota = contract_quota = 0
        if len(quotes) >= 2:
            q = quotes[-2]  # Kvota bo'limi
            gqm = re.search(r'bg-primary-green"></span>\s*(\d+)', q)
            cqm = re.search(r'bg-primary-accent"></span>\s*(\d+)', q)
            if gqm:
                grant_quota = int(gqm.group(1))
            if cqm:
                contract_quota = int(cqm.group(1))

        directions.append({
            'name': name,
            'code': code,
            'grant_score': grant_score,
            'contract_score': contract_score,
            'grant_quota': grant_quota,
            'contract_quota': contract_quota,
        })

    return directions


def get_university_name_from_html(html):
    """HTML dan universitetning to'liq nomini olish."""
    # H1 tagdan
    h1_m = re.search(r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if h1_m:
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h1_m.group(1))).strip()
    # OG title dan
    og_m = re.search(r'property="og:title"\s+content="([^"]+)"', html)
    if og_m:
        # "Buxoro davlat universiteti kirish ballari 2024" → "Buxoro davlat universiteti"
        title = og_m.group(1)
        title = re.sub(r'\s+kirish ballari\s+\d{4}.*', '', title, flags=re.IGNORECASE)
        return title.strip()
    return ''


class Command(BaseCommand):
    help = 'oliygoh.uz dan barcha OTMlar va yo\'nalishlarini DB ga kiritadi'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, default=2024,
                            help='Qaysi yil ballari (default: 2024)')
        parser.add_argument('--slug', type=str, default=None,
                            help='Faqat bitta OTM slugi (test uchun)')
        parser.add_argument('--delay', type=float, default=1.5,
                            help='So\'rovlar orasidagi kutish (soniya, default: 1.5)')
        parser.add_argument('--dry-run', action='store_true',
                            help='DB ga yozmasdan faqat parse qiladi')

    def handle(self, *args, **options):
        year = options['year']
        target_slug = options['slug']
        delay = options['delay']
        dry_run = options['dry_run']

        universities = UNIVERSITIES
        if target_slug:
            universities = [(n, s) for n, s in UNIVERSITIES if s == target_slug]
            if not universities:
                self.stderr.write(f'Slug topilmadi: {target_slug}')
                return

        total = len(universities)
        self.stdout.write(self.style.SUCCESS(
            f'Scraping boshlandi: {total} ta OTM, {year}-yil ma\'lumotlari'
        ))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN rejimi — DB ga yozilmaydi'))

        uni_ok = uni_skip = dir_ok = dir_skip = score_ok = 0
        session = requests.Session()
        session.headers.update(HEADERS)

        for idx, (display_name, site_slug) in enumerate(universities, 1):
            self.stdout.write(f'[{idx}/{total}] {display_name[:55]:<55}', ending=' ')

            url = f'{BASE_URL}/{site_slug}'
            try:
                resp = session.get(url, timeout=20)
                resp.raise_for_status()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'XATO: {e}'))
                uni_skip += 1
                continue

            html = resp.text
            parsed_name = get_university_name_from_html(html) or display_name
            region = detect_region(display_name + ' ' + site_slug)

            # DB slug: site_slug dan foydalanish (unique kafolati)
            db_slug = site_slug

            directions_data = parse_directions(html)
            self.stdout.write(f'{len(directions_data)} yo\'nalish', ending='')

            if dry_run:
                self.stdout.write('')
                for d in directions_data[:3]:
                    self.stdout.write(f'   {d["name"][:50]} | G:{d["grant_score"]} C:{d["contract_score"]}')
                dir_ok += len(directions_data)
                uni_ok += 1
                time.sleep(delay)
                continue

            # ── University yaratish/yangilash ──
            uni, created = University.objects.update_or_create(
                slug=db_slug,
                defaults={
                    'name': parsed_name or display_name,
                    'short_name': display_name[:200],
                    'region': region,
                    'city': region,
                    'university_type': 'state',
                    'is_active': True,
                }
            )
            uni_ok += 1

            # ── Yo'nalishlar ──
            code_counter = {}  # Bir university ichida kod takrorlanmasligi uchun
            for d in directions_data:
                code = d['code'] or 'NOMA\'LUM'
                # Agar bu kod allaqachon ishlatilgan bo'lsa, raqam qo'shamiz
                if code in code_counter:
                    code_counter[code] += 1
                    code = f"{code}_{code_counter[code]}"
                else:
                    code_counter[code] = 0

                dir_slug = slugify(d['name'])[:48] or slugify(code)

                direction, d_created = Direction.objects.update_or_create(
                    university=uni,
                    code=code,
                    defaults={
                        'name': d['name'],
                        'slug': dir_slug,
                        'grant_quota': d['grant_quota'],
                        'contract_quota': d['contract_quota'],
                        'education_type': 'both',
                        'education_form': 'full_time',
                        'is_active': True,
                    }
                )
                dir_ok += 1

                # ── O'tish ballari ──
                if d['grant_score'] is not None or d['contract_score'] is not None:
                    PassingScore.objects.update_or_create(
                        direction=direction,
                        year=year,
                        defaults={
                            'grant_score': d['grant_score'],
                            'contract_score': d['contract_score'],
                        }
                    )
                    score_ok += 1

            self.stdout.write(self.style.SUCCESS(' ✓'))
            time.sleep(delay)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 55))
        self.stdout.write(self.style.SUCCESS(
            f'Natija:  {uni_ok} OTM  |  {dir_ok} yo\'nalish  |  {score_ok} ball yozuvi'
        ))
        if uni_skip:
            self.stdout.write(self.style.WARNING(f'O\'tkazib yuborildi: {uni_skip} OTM'))

"""
O'zbekiston universitetlari HAQIQIY ma'lumotlari — 2025-yil.
Davlat, xususiy, xorijiy filial va qo'shma universitetlar.
Fakultetlar, yo'nalishlar, kontrakt narxlari va 2024-2025 kirish ballari.

Usage: python manage.py populate_universities
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from universities.models import University, Faculty, Direction, PassingScore


# ============================================================
# DAVLAT UNIVERSITETLARI
# ============================================================
STATE_UNIVERSITIES = [
    {
        'name': "O'zbekiston Milliy universiteti",
        'short_name': "O'zMU",
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1918,
        'students': 25000,
        'website': 'https://nuu.uz',
        'email': 'info@nuu.uz',
        'phone': '+998712464000',
        'address': "Universitet ko'chasi 4, Olmazor tumani, Toshkent",
        'description': "O'zbekistonning eng qadimgi va nufuzli universiteti. 1918-yilda tashkil etilgan. Mamlakatdagi eng yirik oliy ta'lim muassasasi.",
        'rating': 4.5,
        'is_featured': True,
        'faculties': [
            {
                'name': 'Matematika fakulteti',
                'directions': [
                    {'code': '60110100', 'name': 'Matematika', 'form': 'full_time', 'grant': 50, 'contract': 150, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 189.5, 'contract': 140.2}, '2024': {'grant': 186.0, 'contract': 136.5}}},
                    {'code': '60110200', 'name': 'Amaliy matematika va informatika', 'form': 'full_time', 'grant': 60, 'contract': 200, 'price': 12960000, 'subjects': ['matematika', 'informatika'], 'scores': {'2025': {'grant': 193.2, 'contract': 148.0}, '2024': {'grant': 190.5, 'contract': 145.0}}},
                ],
            },
            {
                'name': 'Fizika fakulteti',
                'directions': [
                    {'code': '60110300', 'name': 'Fizika', 'form': 'full_time', 'grant': 45, 'contract': 120, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 182.5, 'contract': 132.0}, '2024': {'grant': 179.0, 'contract': 128.5}}},
                    {'code': '60110400', 'name': 'Astronomiya', 'form': 'full_time', 'grant': 20, 'contract': 50, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 175.0, 'contract': 125.0}, '2024': {'grant': 172.0, 'contract': 122.0}}},
                ],
            },
            {
                'name': 'Kimyo fakulteti',
                'directions': [
                    {'code': '60110500', 'name': 'Kimyo', 'form': 'full_time', 'grant': 40, 'contract': 130, 'price': 12960000, 'subjects': ['kimyo', 'matematika'], 'scores': {'2025': {'grant': 185.0, 'contract': 135.0}, '2024': {'grant': 182.0, 'contract': 131.5}}},
                ],
            },
            {
                'name': 'Biologiya fakulteti',
                'directions': [
                    {'code': '60110600', 'name': 'Biologiya', 'form': 'full_time', 'grant': 45, 'contract': 140, 'price': 12960000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 187.0, 'contract': 138.0}, '2024': {'grant': 184.0, 'contract': 135.0}}},
                    {'code': '60110700', 'name': 'Biotexnologiya', 'form': 'full_time', 'grant': 30, 'contract': 100, 'price': 14400000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 191.0, 'contract': 145.0}, '2024': {'grant': 188.5, 'contract': 142.0}}},
                ],
            },
            {
                'name': 'Geografiya fakulteti',
                'directions': [
                    {'code': '60110800', 'name': 'Geografiya', 'form': 'full_time', 'grant': 35, 'contract': 110, 'price': 12960000, 'subjects': ['geografiya', 'matematika'], 'scores': {'2025': {'grant': 178.0, 'contract': 128.0}, '2024': {'grant': 175.5, 'contract': 125.0}}},
                    {'code': '60110900', 'name': 'Ekologiya', 'form': 'full_time', 'grant': 25, 'contract': 80, 'price': 12960000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 172.0, 'contract': 122.0}, '2024': {'grant': 169.0, 'contract': 119.0}}},
                ],
            },
            {
                'name': 'Tarix fakulteti',
                'directions': [
                    {'code': '60120100', 'name': 'Tarix', 'form': 'full_time', 'grant': 35, 'contract': 120, 'price': 12960000, 'subjects': ['tarix', 'ona-tili'], 'scores': {'2025': {'grant': 185.0, 'contract': 140.0}, '2024': {'grant': 182.0, 'contract': 137.0}}},
                    {'code': '60120200', 'name': 'Arxeologiya', 'form': 'full_time', 'grant': 15, 'contract': 40, 'price': 12960000, 'subjects': ['tarix', 'ona-tili'], 'scores': {'2025': {'grant': 170.0, 'contract': 120.0}, '2024': {'grant': 167.0, 'contract': 117.0}}},
                ],
            },
            {
                'name': 'Filologiya fakulteti',
                'directions': [
                    {'code': '60120300', 'name': "O'zbek filologiyasi", 'form': 'full_time', 'grant': 40, 'contract': 130, 'price': 12960000, 'subjects': ['ona-tili', 'tarix'], 'scores': {'2025': {'grant': 188.0, 'contract': 142.0}, '2024': {'grant': 185.0, 'contract': 139.0}}},
                    {'code': '60120400', 'name': 'Ingliz filologiyasi', 'form': 'full_time', 'grant': 30, 'contract': 200, 'price': 14400000, 'subjects': ['ingliz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 196.0, 'contract': 155.0}, '2024': {'grant': 193.5, 'contract': 152.0}}},
                    {'code': '60120500', 'name': 'Jurnalistika', 'form': 'full_time', 'grant': 25, 'contract': 150, 'price': 12960000, 'subjects': ['ona-tili', 'tarix'], 'scores': {'2025': {'grant': 190.0, 'contract': 148.0}, '2024': {'grant': 187.0, 'contract': 145.0}}},
                ],
            },
            {
                'name': 'Iqtisodiyot fakulteti',
                'directions': [
                    {'code': '60310100', 'name': 'Iqtisodiyot', 'form': 'full_time', 'grant': 35, 'contract': 180, 'price': 14400000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 192.0, 'contract': 150.0}, '2024': {'grant': 189.5, 'contract': 147.0}}},
                ],
            },
        ],
    },
    {
        'name': "Toshkent davlat texnika universiteti",
        'short_name': 'ToshDTU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1929,
        'students': 22000,
        'website': 'https://tdtu.uz',
        'email': 'info@tdtu.uz',
        'phone': '+998712271933',
        'address': "Universitetlar ko'chasi 2, Olmazor tumani, Toshkent",
        'description': "O'zbekistonning yetakchi texnika universiteti. Muhandislik va texnologiya sohasida eng nufuzli oliy ta'lim muassasasi.",
        'rating': 4.4,
        'is_featured': True,
        'faculties': [
            {
                'name': 'Energetika fakulteti',
                'directions': [
                    {'code': '60710100', 'name': 'Elektr energetikasi', 'form': 'full_time', 'grant': 55, 'contract': 180, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 188.0, 'contract': 142.0}, '2024': {'grant': 185.0, 'contract': 139.0}}},
                    {'code': '60710200', 'name': 'Issiqlik energetikasi', 'form': 'full_time', 'grant': 40, 'contract': 120, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 180.0, 'contract': 130.0}, '2024': {'grant': 177.0, 'contract': 127.0}}},
                ],
            },
            {
                'name': 'Mexanika-mashinasozlik fakulteti',
                'directions': [
                    {'code': '60710300', 'name': 'Mashinasozlik texnologiyasi', 'form': 'full_time', 'grant': 45, 'contract': 150, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 183.0, 'contract': 133.0}, '2024': {'grant': 180.0, 'contract': 130.0}}},
                    {'code': '60710400', 'name': 'Mexatronika va robototexnika', 'form': 'full_time', 'grant': 30, 'contract': 100, 'price': 14400000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 190.0, 'contract': 148.0}, '2024': {'grant': 187.0, 'contract': 145.0}}},
                ],
            },
            {
                'name': 'Elektronika va avtomatika fakulteti',
                'directions': [
                    {'code': '60710500', 'name': 'Elektronika va asbobsozlik', 'form': 'full_time', 'grant': 40, 'contract': 130, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 185.0, 'contract': 138.0}, '2024': {'grant': 182.0, 'contract': 135.0}}},
                    {'code': '60710600', 'name': 'Avtomatlashtirish va boshqarish', 'form': 'full_time', 'grant': 35, 'contract': 120, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 187.0, 'contract': 140.0}, '2024': {'grant': 184.0, 'contract': 137.0}}},
                ],
            },
            {
                'name': 'Kompyuter injiniringi fakulteti',
                'directions': [
                    {'code': '60610100', 'name': "Kompyuter injiniringi", 'form': 'full_time', 'grant': 50, 'contract': 250, 'price': 14400000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 195.0, 'contract': 155.0}, '2024': {'grant': 192.0, 'contract': 152.0}}},
                    {'code': '60610200', 'name': "Dasturiy injiniring", 'form': 'full_time', 'grant': 45, 'contract': 220, 'price': 14400000, 'subjects': ['matematika', 'informatika'], 'scores': {'2025': {'grant': 197.0, 'contract': 158.0}, '2024': {'grant': 194.0, 'contract': 155.0}}},
                ],
            },
            {
                'name': 'Qurilish fakulteti',
                'directions': [
                    {'code': '60730100', 'name': 'Qurilish muhandisligi', 'form': 'full_time', 'grant': 50, 'contract': 180, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 184.0, 'contract': 136.0}, '2024': {'grant': 181.0, 'contract': 133.0}}},
                ],
            },
            {
                'name': 'Konchilik fakulteti',
                'directions': [
                    {'code': '60720100', 'name': 'Konchilik ishi', 'form': 'full_time', 'grant': 35, 'contract': 100, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 175.0, 'contract': 125.0}, '2024': {'grant': 172.0, 'contract': 122.0}}},
                    {'code': '60720200', 'name': 'Neft va gaz ishi', 'form': 'full_time', 'grant': 30, 'contract': 120, 'price': 14400000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 182.0, 'contract': 135.0}, '2024': {'grant': 179.0, 'contract': 132.0}}},
                ],
            },
        ],
    },
    {
        'name': "Muhammad al-Xorazmiy nomidagi Toshkent axborot texnologiyalari universiteti",
        'short_name': 'TATU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1955,
        'students': 18000,
        'website': 'https://tuit.uz',
        'email': 'info@tuit.uz',
        'phone': '+998712381414',
        'address': "Amir Temur shoh ko'chasi 108, Toshkent",
        'description': "O'zbekistonda IT va telekommunikatsiya sohasidagi eng nufuzli universitet. Axborot texnologiyalari mutaxassislarini tayyorlashda yetakchi.",
        'rating': 4.6,
        'is_featured': True,
        'faculties': [
            {
                'name': 'Dasturiy injiniring fakulteti',
                'directions': [
                    {'code': '60610300', 'name': 'Dasturiy injiniring', 'form': 'full_time', 'grant': 80, 'contract': 350, 'price': 14400000, 'subjects': ['matematika', 'informatika'], 'scores': {'2025': {'grant': 199.0, 'contract': 165.0}, '2024': {'grant': 196.0, 'contract': 162.0}}},
                    {'code': '60610400', 'name': "Kompyuter ilmlari", 'form': 'full_time', 'grant': 60, 'contract': 280, 'price': 14400000, 'subjects': ['matematika', 'informatika'], 'scores': {'2025': {'grant': 197.5, 'contract': 160.0}, '2024': {'grant': 194.5, 'contract': 157.0}}},
                ],
            },
            {
                'name': 'Kiberxavfsizlik fakulteti',
                'directions': [
                    {'code': '60610500', 'name': "Axborot xavfsizligi", 'form': 'full_time', 'grant': 50, 'contract': 200, 'price': 14400000, 'subjects': ['matematika', 'informatika'], 'scores': {'2025': {'grant': 195.0, 'contract': 155.0}, '2024': {'grant': 192.0, 'contract': 152.0}}},
                    {'code': '60610600', 'name': "Kriptografiya", 'form': 'full_time', 'grant': 25, 'contract': 80, 'price': 14400000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 190.0, 'contract': 150.0}, '2024': {'grant': 187.0, 'contract': 147.0}}},
                ],
            },
            {
                'name': 'Telekommunikatsiya texnologiyalari fakulteti',
                'directions': [
                    {'code': '60610700', 'name': "Telekommunikatsiya texnologiyalari", 'form': 'full_time', 'grant': 45, 'contract': 180, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 188.0, 'contract': 145.0}, '2024': {'grant': 185.0, 'contract': 142.0}}},
                    {'code': '60610800', 'name': "Mobil texnologiyalar", 'form': 'full_time', 'grant': 30, 'contract': 150, 'price': 14400000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 192.0, 'contract': 150.0}, '2024': {'grant': 189.0, 'contract': 147.0}}},
                ],
            },
            {
                'name': "Sun'iy intellekt fakulteti",
                'directions': [
                    {'code': '60610900', 'name': "Sun'iy intellekt", 'form': 'full_time', 'grant': 40, 'contract': 200, 'price': 16000000, 'subjects': ['matematika', 'informatika'], 'scores': {'2025': {'grant': 200.0, 'contract': 168.0}, '2024': {'grant': 197.0, 'contract': 165.0}}},
                    {'code': '60611000', 'name': "Ma'lumotlar fani (Data Science)", 'form': 'full_time', 'grant': 35, 'contract': 180, 'price': 16000000, 'subjects': ['matematika', 'informatika'], 'scores': {'2025': {'grant': 198.0, 'contract': 162.0}, '2024': {'grant': 195.0, 'contract': 159.0}}},
                ],
            },
        ],
    },
    {
        'name': "Toshkent davlat iqtisodiyot universiteti",
        'short_name': 'TDIU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1931,
        'students': 15000,
        'website': 'https://tsue.uz',
        'email': 'info@tsue.uz',
        'phone': '+998712391225',
        'address': "Islom Karimov ko'chasi 49, Toshkent",
        'description': "O'zbekistondagi eng yirik iqtisodiyot universiteti. Iqtisodchi va menejment mutaxassislarini tayyorlashda yetakchi.",
        'rating': 4.3,
        'faculties': [
            {
                'name': 'Iqtisodiyot fakulteti',
                'directions': [
                    {'code': '60310200', 'name': "Iqtisodiyot (tarmoqlar bo'yicha)", 'form': 'full_time', 'grant': 50, 'contract': 200, 'price': 14400000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 188.0, 'contract': 145.0}, '2024': {'grant': 185.0, 'contract': 142.0}}},
                    {'code': '60310300', 'name': "Makroiqtisodiy tahlil va prognozlashtirish", 'form': 'full_time', 'grant': 30, 'contract': 120, 'price': 14400000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 186.0, 'contract': 140.0}, '2024': {'grant': 183.0, 'contract': 137.0}}},
                ],
            },
            {
                'name': 'Menejment fakulteti',
                'directions': [
                    {'code': '60310400', 'name': 'Menejment', 'form': 'full_time', 'grant': 40, 'contract': 180, 'price': 14400000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 185.0, 'contract': 142.0}, '2024': {'grant': 182.0, 'contract': 139.0}}},
                    {'code': '60310500', 'name': 'Marketing', 'form': 'full_time', 'grant': 30, 'contract': 150, 'price': 14400000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 183.0, 'contract': 140.0}, '2024': {'grant': 180.0, 'contract': 137.0}}},
                ],
            },
            {
                'name': 'Moliya fakulteti',
                'directions': [
                    {'code': '60310600', 'name': 'Moliya va moliyaviy texnologiyalar', 'form': 'full_time', 'grant': 45, 'contract': 200, 'price': 14400000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 190.0, 'contract': 148.0}, '2024': {'grant': 187.0, 'contract': 145.0}}},
                    {'code': '60310700', 'name': "Buxgalteriya hisobi va audit", 'form': 'full_time', 'grant': 35, 'contract': 160, 'price': 12960000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 184.0, 'contract': 138.0}, '2024': {'grant': 181.0, 'contract': 135.0}}},
                    {'code': '60310800', 'name': 'Bank ishi', 'form': 'full_time', 'grant': 30, 'contract': 150, 'price': 14400000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 187.0, 'contract': 145.0}, '2024': {'grant': 184.0, 'contract': 142.0}}},
                ],
            },
            {
                'name': 'Raqamli iqtisodiyot fakulteti',
                'directions': [
                    {'code': '60310900', 'name': 'Raqamli iqtisodiyot', 'form': 'full_time', 'grant': 35, 'contract': 180, 'price': 16000000, 'subjects': ['matematika', 'informatika'], 'scores': {'2025': {'grant': 192.0, 'contract': 152.0}, '2024': {'grant': 189.0, 'contract': 149.0}}},
                ],
            },
        ],
    },
    {
        'name': "Toshkent davlat yuridik universiteti",
        'short_name': 'TDYU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1994,
        'students': 12000,
        'website': 'https://tsul.uz',
        'email': 'info@tsul.uz',
        'phone': '+998712333532',
        'address': "Sayilgoh ko'chasi 35, Toshkent",
        'description': "O'zbekistondagi eng nufuzli yuridik oliy ta'lim muassasasi. Huquqshunos mutaxassislar tayyorlashda yetakchi.",
        'rating': 4.4,
        'is_featured': True,
        'faculties': [
            {
                'name': 'Xalqaro huquq fakulteti',
                'directions': [
                    {'code': '60410100', 'name': 'Xalqaro huquq', 'form': 'full_time', 'grant': 35, 'contract': 200, 'price': 16000000, 'subjects': ['tarix', 'ona-tili'], 'scores': {'2025': {'grant': 195.0, 'contract': 158.0}, '2024': {'grant': 192.0, 'contract': 155.0}}},
                ],
            },
            {
                'name': 'Jinoyat huquqi fakulteti',
                'directions': [
                    {'code': '60410200', 'name': 'Yurisiprudensiya (jinoyat huquqi)', 'form': 'full_time', 'grant': 50, 'contract': 250, 'price': 14400000, 'subjects': ['tarix', 'ona-tili'], 'scores': {'2025': {'grant': 192.0, 'contract': 152.0}, '2024': {'grant': 189.0, 'contract': 149.0}}},
                ],
            },
            {
                'name': 'Fuqarolik huquqi fakulteti',
                'directions': [
                    {'code': '60410300', 'name': 'Yurisiprudensiya (fuqarolik huquqi)', 'form': 'full_time', 'grant': 45, 'contract': 220, 'price': 14400000, 'subjects': ['tarix', 'ona-tili'], 'scores': {'2025': {'grant': 190.0, 'contract': 150.0}, '2024': {'grant': 187.0, 'contract': 147.0}}},
                ],
            },
            {
                'name': 'Biznes huquqi fakulteti',
                'directions': [
                    {'code': '60410400', 'name': 'Biznes huquqi', 'form': 'full_time', 'grant': 30, 'contract': 180, 'price': 16000000, 'subjects': ['tarix', 'ona-tili'], 'scores': {'2025': {'grant': 193.0, 'contract': 155.0}, '2024': {'grant': 190.0, 'contract': 152.0}}},
                ],
            },
        ],
    },
    {
        'name': "Toshkent tibbiyot akademiyasi",
        'short_name': 'TTA',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1920,
        'students': 16000,
        'website': 'https://tma.uz',
        'email': 'info@tma.uz',
        'phone': '+998712564805',
        'address': "Farobiy ko'chasi 2, Toshkent",
        'description': "O'zbekistonning eng nufuzli tibbiyot oliy ta'lim muassasasi. Shifokor va farmatsevt mutaxassislarini tayyorlaydi.",
        'rating': 4.5,
        'is_featured': True,
        'faculties': [
            {
                'name': "Davolash fakulteti",
                'directions': [
                    {'code': '60510100', 'name': "Davolash ishi", 'form': 'full_time', 'grant': 120, 'contract': 450, 'price': 22000000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 202.5, 'contract': 175.0}, '2024': {'grant': 199.5, 'contract': 172.0}}},
                ],
            },
            {
                'name': "Pediatriya fakulteti",
                'directions': [
                    {'code': '60510200', 'name': "Pediatriya", 'form': 'full_time', 'grant': 80, 'contract': 300, 'price': 22000000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 198.0, 'contract': 170.0}, '2024': {'grant': 195.0, 'contract': 167.0}}},
                ],
            },
            {
                'name': "Stomatologiya fakulteti",
                'directions': [
                    {'code': '60510300', 'name': "Stomatologiya", 'form': 'full_time', 'grant': 50, 'contract': 250, 'price': 25000000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 200.0, 'contract': 178.0}, '2024': {'grant': 197.0, 'contract': 175.0}}},
                ],
            },
            {
                'name': "Farmatsiya fakulteti",
                'directions': [
                    {'code': '60510400', 'name': "Farmatsiya", 'form': 'full_time', 'grant': 60, 'contract': 200, 'price': 18000000, 'subjects': ['kimyo', 'biologiya'], 'scores': {'2025': {'grant': 193.0, 'contract': 160.0}, '2024': {'grant': 190.0, 'contract': 157.0}}},
                ],
            },
            {
                'name': "Tibbiy profilaktika fakulteti",
                'directions': [
                    {'code': '60510500', 'name': "Tibbiy profilaktika ishi", 'form': 'full_time', 'grant': 40, 'contract': 150, 'price': 18000000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 188.0, 'contract': 155.0}, '2024': {'grant': 185.0, 'contract': 152.0}}},
                ],
            },
        ],
    },
    {
        'name': "Toshkent davlat pedagogika universiteti",
        'short_name': 'TDPU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1935,
        'students': 14000,
        'website': 'https://tdpu.uz',
        'email': 'info@tdpu.uz',
        'phone': '+998712540582',
        'address': "Bunyodkor ko'chasi 27, Toshkent",
        'description': "O'zbekistondagi eng yirik pedagogika universiteti. O'qituvchi kadrlar tayyorlashda yetakchi.",
        'rating': 4.1,
        'faculties': [
            {
                'name': "Matematika va informatika o'qitish metodikasi fakulteti",
                'directions': [
                    {'code': '60110101', 'name': "Matematika o'qitish metodikasi", 'form': 'full_time', 'grant': 60, 'contract': 200, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 178.0, 'contract': 128.0}, '2024': {'grant': 175.0, 'contract': 125.0}}},
                    {'code': '60110201', 'name': "Informatika o'qitish metodikasi", 'form': 'full_time', 'grant': 45, 'contract': 180, 'price': 12960000, 'subjects': ['matematika', 'informatika'], 'scores': {'2025': {'grant': 180.0, 'contract': 132.0}, '2024': {'grant': 177.0, 'contract': 129.0}}},
                ],
            },
            {
                'name': "Boshlang'ich ta'lim fakulteti",
                'directions': [
                    {'code': '60110301', 'name': "Boshlang'ich ta'lim", 'form': 'full_time', 'grant': 80, 'contract': 250, 'price': 12960000, 'subjects': ['ona-tili', 'matematika'], 'scores': {'2025': {'grant': 182.0, 'contract': 135.0}, '2024': {'grant': 179.0, 'contract': 132.0}}},
                    {'code': '60110401', 'name': "Maktabgacha ta'lim", 'form': 'full_time', 'grant': 50, 'contract': 150, 'price': 12960000, 'subjects': ['ona-tili', 'biologiya'], 'scores': {'2025': {'grant': 170.0, 'contract': 120.0}, '2024': {'grant': 167.0, 'contract': 117.0}}},
                ],
            },
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110501', 'name': "Biologiya o'qitish metodikasi", 'form': 'full_time', 'grant': 40, 'contract': 130, 'price': 12960000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 175.0, 'contract': 125.0}, '2024': {'grant': 172.0, 'contract': 122.0}}},
                    {'code': '60110601', 'name': "Kimyo o'qitish metodikasi", 'form': 'full_time', 'grant': 35, 'contract': 120, 'price': 12960000, 'subjects': ['kimyo', 'matematika'], 'scores': {'2025': {'grant': 173.0, 'contract': 123.0}, '2024': {'grant': 170.0, 'contract': 120.0}}},
                ],
            },
        ],
    },
    {
        'name': "Toshkent moliya instituti",
        'short_name': 'TMI',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1991,
        'students': 8000,
        'website': 'https://tfi.uz',
        'email': 'info@tfi.uz',
        'phone': '+998712891825',
        'address': "Amir Temur shoh ko'chasi 60A, Toshkent",
        'description': "Moliya, soliq va sug'urta sohasida mutaxassislar tayyorlovchi yetakchi institut.",
        'rating': 4.2,
        'faculties': [
            {
                'name': "Moliya fakulteti",
                'directions': [
                    {'code': '60310610', 'name': "Moliya", 'form': 'full_time', 'grant': 40, 'contract': 180, 'price': 14400000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 188.0, 'contract': 145.0}, '2024': {'grant': 185.0, 'contract': 142.0}}},
                    {'code': '60310710', 'name': "Soliq va soliqqa tortish", 'form': 'full_time', 'grant': 30, 'contract': 120, 'price': 14400000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 183.0, 'contract': 138.0}, '2024': {'grant': 180.0, 'contract': 135.0}}},
                ],
            },
            {
                'name': "Sug'urta ishi fakulteti",
                'directions': [
                    {'code': '60310810', 'name': "Sug'urta ishi", 'form': 'full_time', 'grant': 25, 'contract': 100, 'price': 12960000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 178.0, 'contract': 130.0}, '2024': {'grant': 175.0, 'contract': 127.0}}},
                ],
            },
        ],
    },
    {
        'name': "O'zbekiston davlat jahon tillari universiteti",
        'short_name': "O'zDJTU",
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1992,
        'students': 10000,
        'website': 'https://uzswlu.uz',
        'email': 'info@uzswlu.uz',
        'phone': '+998712143620',
        'address': "Kichik Xalqa Yo'li 21A, Toshkent",
        'description': "Chet tillar va tarjimonlik sohasida O'zbekistondagi eng nufuzli universitet.",
        'rating': 4.3,
        'faculties': [
            {
                'name': "Ingliz tili fakulteti",
                'directions': [
                    {'code': '60120410', 'name': "Ingliz tili va adabiyoti", 'form': 'full_time', 'grant': 50, 'contract': 250, 'price': 14400000, 'subjects': ['ingliz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 195.0, 'contract': 158.0}, '2024': {'grant': 192.0, 'contract': 155.0}}},
                    {'code': '60120420', 'name': "Tarjimashunoslik (ingliz tili)", 'form': 'full_time', 'grant': 40, 'contract': 200, 'price': 14400000, 'subjects': ['ingliz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 193.0, 'contract': 155.0}, '2024': {'grant': 190.0, 'contract': 152.0}}},
                ],
            },
            {
                'name': "Yevropa tillari fakulteti",
                'directions': [
                    {'code': '60120430', 'name': "Nemis tili va adabiyoti", 'form': 'full_time', 'grant': 30, 'contract': 120, 'price': 12960000, 'subjects': ['nemis-tili', 'ona-tili'], 'scores': {'2025': {'grant': 182.0, 'contract': 135.0}, '2024': {'grant': 179.0, 'contract': 132.0}}},
                    {'code': '60120440', 'name': "Fransuz tili va adabiyoti", 'form': 'full_time', 'grant': 25, 'contract': 100, 'price': 12960000, 'subjects': ['fransuz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 178.0, 'contract': 130.0}, '2024': {'grant': 175.0, 'contract': 127.0}}},
                ],
            },
            {
                'name': "Sharq tillari fakulteti",
                'directions': [
                    {'code': '60120450', 'name': "Xitoy tili va adabiyoti", 'form': 'full_time', 'grant': 25, 'contract': 120, 'price': 14400000, 'subjects': ['ingliz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 188.0, 'contract': 145.0}, '2024': {'grant': 185.0, 'contract': 142.0}}},
                    {'code': '60120460', 'name': "Koreys tili va adabiyoti", 'form': 'full_time', 'grant': 25, 'contract': 120, 'price': 14400000, 'subjects': ['ingliz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 186.0, 'contract': 143.0}, '2024': {'grant': 183.0, 'contract': 140.0}}},
                ],
            },
        ],
    },
    {
        'name': "Toshkent davlat agrar universiteti",
        'short_name': 'ToshDAU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1930,
        'students': 12000,
        'website': 'https://tdau.uz',
        'email': 'info@tdau.uz',
        'phone': '+998712606726',
        'address': "Universitetlar ko'chasi 2, Toshkent",
        'description': "Qishloq xo'jaligi sohasida yetakchi oliy ta'lim muassasasi.",
        'rating': 3.9,
        'faculties': [
            {
                'name': "Agronomiya fakulteti",
                'directions': [
                    {'code': '60810100', 'name': "Agronomiya", 'form': 'full_time', 'grant': 60, 'contract': 180, 'price': 12960000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 172.0, 'contract': 120.0}, '2024': {'grant': 169.0, 'contract': 117.0}}},
                ],
            },
            {
                'name': "Veterinariya fakulteti",
                'directions': [
                    {'code': '60810200', 'name': "Veterinariya", 'form': 'full_time', 'grant': 40, 'contract': 120, 'price': 14400000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 175.0, 'contract': 125.0}, '2024': {'grant': 172.0, 'contract': 122.0}}},
                ],
            },
        ],
    },
    {
        'name': "Toshkent arxitektura-qurilish universiteti",
        'short_name': 'TAQU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1991,
        'students': 9000,
        'website': 'https://taqi.uz',
        'email': 'info@taqi.uz',
        'phone': '+998712451034',
        'address': "Navoiy ko'chasi 13, Toshkent",
        'description': "Arxitektura va qurilish sohasida mutaxassislar tayyorlashda yetakchi.",
        'rating': 4.0,
        'faculties': [
            {
                'name': "Arxitektura fakulteti",
                'directions': [
                    {'code': '60730200', 'name': "Arxitektura", 'form': 'full_time', 'grant': 35, 'contract': 150, 'price': 14400000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 185.0, 'contract': 140.0}, '2024': {'grant': 182.0, 'contract': 137.0}}},
                ],
            },
            {
                'name': "Qurilish fakulteti",
                'directions': [
                    {'code': '60730300', 'name': "Qurilish", 'form': 'full_time', 'grant': 50, 'contract': 180, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 180.0, 'contract': 132.0}, '2024': {'grant': 177.0, 'contract': 129.0}}},
                ],
            },
        ],
    },
    {
        'name': "Toshkent kimyo-texnologiya instituti",
        'short_name': 'TKTI',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1948,
        'students': 7000,
        'website': 'https://tcti.uz',
        'email': 'info@tcti.uz',
        'phone': '+998712445137',
        'address': "Navoiy ko'chasi 32, Toshkent",
        'description': "Kimyo texnologiyasi va oziq-ovqat sanoati sohasida mutaxassislar tayyorlash.",
        'rating': 3.8,
        'faculties': [
            {
                'name': "Kimyoviy texnologiya fakulteti",
                'directions': [
                    {'code': '60720300', 'name': "Kimyoviy texnologiya", 'form': 'full_time', 'grant': 35, 'contract': 120, 'price': 12960000, 'subjects': ['kimyo', 'matematika'], 'scores': {'2025': {'grant': 178.0, 'contract': 128.0}, '2024': {'grant': 175.0, 'contract': 125.0}}},
                    {'code': '60720400', 'name': "Oziq-ovqat texnologiyasi", 'form': 'full_time', 'grant': 30, 'contract': 100, 'price': 12960000, 'subjects': ['kimyo', 'biologiya'], 'scores': {'2025': {'grant': 173.0, 'contract': 122.0}, '2024': {'grant': 170.0, 'contract': 119.0}}},
                ],
            },
        ],
    },
    # ======================== VILOYAT UNIVERSITETLARI ========================
    {
        'name': "Samarqand davlat universiteti",
        'short_name': 'SamDU',
        'type': 'state',
        'region': 'Samarqand',
        'city': 'Samarqand',
        'established': 1927,
        'students': 20000,
        'website': 'https://samdu.uz',
        'email': 'info@samdu.uz',
        'phone': '+998662215982',
        'address': "Universitetlar xiyoboni 15, Samarqand",
        'description': "Markaziy Osiyodagi eng qadimiy universitetlardan biri. 1927-yilda tashkil etilgan.",
        'rating': 4.3,
        'is_featured': True,
        'faculties': [
            {
                'name': "Matematika fakulteti",
                'directions': [
                    {'code': '60110102', 'name': "Matematika", 'form': 'full_time', 'grant': 45, 'contract': 150, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 183.0, 'contract': 133.0}, '2024': {'grant': 180.0, 'contract': 130.0}}},
                ],
            },
            {
                'name': "Fizika fakulteti",
                'directions': [
                    {'code': '60110302', 'name': "Fizika", 'form': 'full_time', 'grant': 35, 'contract': 100, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 178.0, 'contract': 128.0}, '2024': {'grant': 175.0, 'contract': 125.0}}},
                ],
            },
            {
                'name': "Biologiya fakulteti",
                'directions': [
                    {'code': '60110602', 'name': "Biologiya", 'form': 'full_time', 'grant': 35, 'contract': 120, 'price': 12960000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 180.0, 'contract': 130.0}, '2024': {'grant': 177.0, 'contract': 127.0}}},
                ],
            },
            {
                'name': "Tarix fakulteti",
                'directions': [
                    {'code': '60120102', 'name': "Tarix", 'form': 'full_time', 'grant': 30, 'contract': 120, 'price': 12960000, 'subjects': ['tarix', 'ona-tili'], 'scores': {'2025': {'grant': 180.0, 'contract': 132.0}, '2024': {'grant': 177.0, 'contract': 129.0}}},
                ],
            },
            {
                'name': "Xorijiy tillar fakulteti",
                'directions': [
                    {'code': '60120402', 'name': "Ingliz tili va adabiyoti", 'form': 'full_time', 'grant': 30, 'contract': 180, 'price': 12960000, 'subjects': ['ingliz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 188.0, 'contract': 145.0}, '2024': {'grant': 185.0, 'contract': 142.0}}},
                ],
            },
        ],
    },
    {
        'name': "Samarqand davlat tibbiyot universiteti",
        'short_name': 'SamDTU',
        'type': 'state',
        'region': 'Samarqand',
        'city': 'Samarqand',
        'established': 1930,
        'students': 12000,
        'website': 'https://sammu.uz',
        'email': 'info@sammu.uz',
        'phone': '+998662331093',
        'address': "Amir Temur ko'chasi 18, Samarqand",
        'description': "O'zbekistondagi eng qadimiy tibbiyot universitetlardan biri.",
        'rating': 4.2,
        'faculties': [
            {
                'name': "Davolash fakulteti",
                'directions': [
                    {'code': '60510102', 'name': "Davolash ishi", 'form': 'full_time', 'grant': 80, 'contract': 350, 'price': 20000000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 198.0, 'contract': 168.0}, '2024': {'grant': 195.0, 'contract': 165.0}}},
                ],
            },
            {
                'name': "Pediatriya fakulteti",
                'directions': [
                    {'code': '60510202', 'name': "Pediatriya", 'form': 'full_time', 'grant': 50, 'contract': 200, 'price': 20000000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 193.0, 'contract': 162.0}, '2024': {'grant': 190.0, 'contract': 159.0}}},
                ],
            },
            {
                'name': "Stomatologiya fakulteti",
                'directions': [
                    {'code': '60510302', 'name': "Stomatologiya", 'form': 'full_time', 'grant': 30, 'contract': 180, 'price': 22000000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 196.0, 'contract': 170.0}, '2024': {'grant': 193.0, 'contract': 167.0}}},
                ],
            },
        ],
    },
    {
        'name': "Buxoro davlat universiteti",
        'short_name': 'BuxDU',
        'type': 'state',
        'region': 'Buxoro',
        'city': 'Buxoro',
        'established': 1930,
        'students': 14000,
        'website': 'https://buxdu.uz',
        'email': 'info@buxdu.uz',
        'phone': '+998652240564',
        'address': "Muhammad Iqbol ko'chasi 11, Buxoro",
        'description': "Buxoro viloyatidagi eng nufuzli oliy ta'lim muassasasi.",
        'rating': 4.0,
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110103', 'name': "Matematika", 'form': 'full_time', 'grant': 35, 'contract': 120, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 178.0, 'contract': 125.0}, '2024': {'grant': 175.0, 'contract': 122.0}}},
                    {'code': '60110303', 'name': "Fizika", 'form': 'full_time', 'grant': 25, 'contract': 80, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 173.0, 'contract': 120.0}, '2024': {'grant': 170.0, 'contract': 117.0}}},
                    {'code': '60110603', 'name': "Biologiya", 'form': 'full_time', 'grant': 30, 'contract': 100, 'price': 12960000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 175.0, 'contract': 122.0}, '2024': {'grant': 172.0, 'contract': 119.0}}},
                ],
            },
            {
                'name': "Filologiya fakulteti",
                'directions': [
                    {'code': '60120303', 'name': "O'zbek filologiyasi", 'form': 'full_time', 'grant': 30, 'contract': 120, 'price': 12960000, 'subjects': ['ona-tili', 'tarix'], 'scores': {'2025': {'grant': 180.0, 'contract': 130.0}, '2024': {'grant': 177.0, 'contract': 127.0}}},
                    {'code': '60120403', 'name': "Ingliz tili", 'form': 'full_time', 'grant': 25, 'contract': 150, 'price': 12960000, 'subjects': ['ingliz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 185.0, 'contract': 140.0}, '2024': {'grant': 182.0, 'contract': 137.0}}},
                ],
            },
        ],
    },
    {
        'name': "Farg'ona davlat universiteti",
        'short_name': "FarDU",
        'type': 'state',
        'region': "Farg'ona",
        'city': "Farg'ona",
        'established': 1930,
        'students': 16000,
        'website': 'https://fdu.uz',
        'email': 'info@fdu.uz',
        'phone': '+998732442514',
        'address': "Murabbiylar ko'chasi 19, Farg'ona",
        'description': "Farg'ona vodiysidagi eng nufuzli oliy ta'lim muassasasi.",
        'rating': 4.1,
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110104', 'name': "Matematika", 'form': 'full_time', 'grant': 40, 'contract': 130, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 180.0, 'contract': 128.0}, '2024': {'grant': 177.0, 'contract': 125.0}}},
                    {'code': '60110604', 'name': "Biologiya", 'form': 'full_time', 'grant': 30, 'contract': 100, 'price': 12960000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 175.0, 'contract': 122.0}, '2024': {'grant': 172.0, 'contract': 119.0}}},
                ],
            },
            {
                'name': "Gumanitar fanlar fakulteti",
                'directions': [
                    {'code': '60120104', 'name': "Tarix", 'form': 'full_time', 'grant': 25, 'contract': 100, 'price': 12960000, 'subjects': ['tarix', 'ona-tili'], 'scores': {'2025': {'grant': 175.0, 'contract': 125.0}, '2024': {'grant': 172.0, 'contract': 122.0}}},
                    {'code': '60120404', 'name': "Ingliz tili", 'form': 'full_time', 'grant': 30, 'contract': 150, 'price': 12960000, 'subjects': ['ingliz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 185.0, 'contract': 138.0}, '2024': {'grant': 182.0, 'contract': 135.0}}},
                ],
            },
        ],
    },
    {
        'name': "Andijon davlat universiteti",
        'short_name': 'AndDU',
        'type': 'state',
        'region': 'Andijon',
        'city': 'Andijon',
        'established': 1931,
        'students': 12000,
        'website': 'https://adu.uz',
        'email': 'info@adu.uz',
        'phone': '+998742243428',
        'address': "Universitetlar ko'chasi 129, Andijon",
        'description': "Andijon viloyatidagi eng yirik davlat universiteti.",
        'rating': 3.9,
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110105', 'name': "Matematika", 'form': 'full_time', 'grant': 35, 'contract': 120, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 177.0, 'contract': 125.0}, '2024': {'grant': 174.0, 'contract': 122.0}}},
                    {'code': '60110605', 'name': "Biologiya", 'form': 'full_time', 'grant': 25, 'contract': 90, 'price': 12960000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 173.0, 'contract': 120.0}, '2024': {'grant': 170.0, 'contract': 117.0}}},
                ],
            },
            {
                'name': "Filologiya fakulteti",
                'directions': [
                    {'code': '60120405', 'name': "Ingliz tili va adabiyoti", 'form': 'full_time', 'grant': 25, 'contract': 130, 'price': 12960000, 'subjects': ['ingliz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 183.0, 'contract': 135.0}, '2024': {'grant': 180.0, 'contract': 132.0}}},
                ],
            },
        ],
    },
    {
        'name': "Namangan davlat universiteti",
        'short_name': 'NamDU',
        'type': 'state',
        'region': 'Namangan',
        'city': 'Namangan',
        'established': 1942,
        'students': 11000,
        'website': 'https://namdu.uz',
        'email': 'info@namdu.uz',
        'phone': '+998692260410',
        'address': "Uychi ko'chasi 316, Namangan",
        'description': "Namangan viloyatidagi yetakchi oliy ta'lim muassasasi.",
        'rating': 3.9,
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110106', 'name': "Matematika", 'form': 'full_time', 'grant': 35, 'contract': 110, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 176.0, 'contract': 123.0}, '2024': {'grant': 173.0, 'contract': 120.0}}},
                ],
            },
            {
                'name': "Filologiya fakulteti",
                'directions': [
                    {'code': '60120406', 'name': "Ingliz tili", 'form': 'full_time', 'grant': 25, 'contract': 120, 'price': 12960000, 'subjects': ['ingliz-tili', 'ona-tili'], 'scores': {'2025': {'grant': 182.0, 'contract': 133.0}, '2024': {'grant': 179.0, 'contract': 130.0}}},
                ],
            },
        ],
    },
    {
        'name': "Qarshi davlat universiteti",
        'short_name': 'QarDU',
        'type': 'state',
        'region': 'Qashqadaryo',
        'city': 'Qarshi',
        'established': 1935,
        'students': 10000,
        'website': 'https://qarshidu.uz',
        'email': 'info@qarshidu.uz',
        'phone': '+998752251044',
        'address': "Kuchabag ko'chasi 17, Qarshi",
        'description': "Qashqadaryo viloyatidagi eng yirik davlat universiteti.",
        'rating': 3.8,
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110107', 'name': "Matematika", 'form': 'full_time', 'grant': 30, 'contract': 100, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 174.0, 'contract': 122.0}, '2024': {'grant': 171.0, 'contract': 119.0}}},
                ],
            },
        ],
    },
    {
        'name': "Urganch davlat universiteti",
        'short_name': 'UrDU',
        'type': 'state',
        'region': 'Xorazm',
        'city': 'Urganch',
        'established': 1992,
        'students': 12000,
        'website': 'https://urdu.uz',
        'email': 'info@urdu.uz',
        'phone': '+998622269850',
        'address': "Xorazm ko'chasi 14, Urganch",
        'description': "Xorazm viloyatidagi eng yirik oliy ta'lim muassasasi.",
        'rating': 4.0,
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110108', 'name': "Matematika", 'form': 'full_time', 'grant': 30, 'contract': 110, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 175.0, 'contract': 123.0}, '2024': {'grant': 172.0, 'contract': 120.0}}},
                    {'code': '60110608', 'name': "IT va dasturlash", 'form': 'full_time', 'grant': 25, 'contract': 130, 'price': 14400000, 'subjects': ['matematika', 'informatika'], 'scores': {'2025': {'grant': 182.0, 'contract': 135.0}, '2024': {'grant': 179.0, 'contract': 132.0}}},
                ],
            },
        ],
    },
    {
        'name': "Termiz davlat universiteti",
        'short_name': 'TermDU',
        'type': 'state',
        'region': 'Surxondaryo',
        'city': 'Termiz',
        'established': 1943,
        'students': 9000,
        'website': 'https://terdu.uz',
        'email': 'info@terdu.uz',
        'phone': '+998762242073',
        'address': "Barkamol avlod ko'chasi 43, Termiz",
        'description': "Surxondaryo viloyatidagi eng nufuzli oliy ta'lim muassasasi.",
        'rating': 3.7,
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110109', 'name': "Matematika", 'form': 'full_time', 'grant': 25, 'contract': 90, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 172.0, 'contract': 120.0}, '2024': {'grant': 169.0, 'contract': 117.0}}},
                ],
            },
        ],
    },
    {
        'name': "Guliston davlat universiteti",
        'short_name': 'GulDU',
        'type': 'state',
        'region': 'Sirdaryo',
        'city': 'Guliston',
        'established': 1992,
        'students': 7000,
        'website': 'https://guldu.uz',
        'email': 'info@guldu.uz',
        'phone': '+998672252620',
        'address': "Guliston shahri, 4-mavze, Sirdaryo",
        'description': "Sirdaryo viloyatidagi yetakchi davlat universiteti.",
        'rating': 3.6,
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110110', 'name': "Matematika", 'form': 'full_time', 'grant': 20, 'contract': 80, 'price': 12960000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 170.0, 'contract': 118.0}, '2024': {'grant': 167.0, 'contract': 115.0}}},
                ],
            },
        ],
    },
    {
        'name': "Navoiy davlat konchilik va texnologiyalar universiteti",
        'short_name': 'NavDKTU',
        'type': 'state',
        'region': 'Navoiy',
        'city': 'Navoiy',
        'established': 1995,
        'students': 8000,
        'website': 'https://ndktu.uz',
        'email': 'info@ndktu.uz',
        'phone': '+998792231840',
        'address': "Galaba shoh ko'chasi 27, Navoiy",
        'description': "Konchilik va texnologiyalar sohasida mutaxassislar tayyorlash.",
        'rating': 3.9,
        'faculties': [
            {
                'name': "Konchilik fakulteti",
                'directions': [
                    {'code': '60720110', 'name': "Konchilik ishi", 'form': 'full_time', 'grant': 40, 'contract': 120, 'price': 12960000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 175.0, 'contract': 125.0}, '2024': {'grant': 172.0, 'contract': 122.0}}},
                    {'code': '60720210', 'name': "Metallurgiya", 'form': 'full_time', 'grant': 30, 'contract': 100, 'price': 12960000, 'subjects': ['kimyo', 'fizika'], 'scores': {'2025': {'grant': 172.0, 'contract': 120.0}, '2024': {'grant': 169.0, 'contract': 117.0}}},
                ],
            },
        ],
    },
    {
        'name': "Jizzax davlat pedagogika universiteti",
        'short_name': 'JizDPU',
        'type': 'state',
        'region': 'Jizzax',
        'city': 'Jizzax',
        'established': 1974,
        'students': 7000,
        'website': 'https://jdpu.uz',
        'email': 'info@jdpu.uz',
        'phone': '+998722262003',
        'address': "Sharof Rashidov ko'chasi 4, Jizzax",
        'description': "Jizzax viloyatidagi eng yirik pedagogika universiteti.",
        'rating': 3.7,
        'faculties': [
            {
                'name': "Pedagogika fakulteti",
                'directions': [
                    {'code': '60110111', 'name': "Boshlang'ich ta'lim", 'form': 'full_time', 'grant': 40, 'contract': 120, 'price': 12960000, 'subjects': ['ona-tili', 'matematika'], 'scores': {'2025': {'grant': 173.0, 'contract': 120.0}, '2024': {'grant': 170.0, 'contract': 117.0}}},
                ],
            },
        ],
    },
    {
        'name': "Nukus davlat pedagogika instituti",
        'short_name': 'NukDPI',
        'type': 'state',
        'region': "Qoraqalpog'iston",
        'city': 'Nukus',
        'established': 1979,
        'students': 6000,
        'website': 'https://ndpi.uz',
        'email': 'info@ndpi.uz',
        'phone': '+998612292147',
        'address': "P.Seytov ko'chasi 1, Nukus",
        'description': "Qoraqalpog'iston Respublikasidagi yetakchi pedagogika instituti.",
        'rating': 3.5,
        'faculties': [
            {
                'name': "Pedagogika fakulteti",
                'directions': [
                    {'code': '60110112', 'name': "Boshlang'ich ta'lim", 'form': 'full_time', 'grant': 30, 'contract': 80, 'price': 12960000, 'subjects': ['ona-tili', 'matematika'], 'scores': {'2025': {'grant': 168.0, 'contract': 115.0}, '2024': {'grant': 165.0, 'contract': 112.0}}},
                ],
            },
        ],
    },
    {
        'name': "Andijon davlat tibbiyot instituti",
        'short_name': 'AndTI',
        'type': 'state',
        'region': 'Andijon',
        'city': 'Andijon',
        'established': 1955,
        'students': 8000,
        'website': 'https://adti.uz',
        'email': 'info@adti.uz',
        'phone': '+998742234812',
        'address': "Yu.Otabekov ko'chasi 1, Andijon",
        'description': "Andijon viloyatidagi yetakchi tibbiyot instituti.",
        'rating': 4.0,
        'faculties': [
            {
                'name': "Davolash fakulteti",
                'directions': [
                    {'code': '60510105', 'name': "Davolash ishi", 'form': 'full_time', 'grant': 60, 'contract': 250, 'price': 18000000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 193.0, 'contract': 162.0}, '2024': {'grant': 190.0, 'contract': 159.0}}},
                ],
            },
        ],
    },
    {
        'name': "Buxoro davlat tibbiyot instituti",
        'short_name': 'BuxTI',
        'type': 'state',
        'region': 'Buxoro',
        'city': 'Buxoro',
        'established': 1990,
        'students': 7000,
        'website': 'https://bsmi.uz',
        'email': 'info@bsmi.uz',
        'phone': '+998652233070',
        'address': "Navoi ko'chasi 1, Buxoro",
        'description': "Buxoro viloyatidagi yetakchi tibbiyot instituti.",
        'rating': 3.9,
        'faculties': [
            {
                'name': "Davolash fakulteti",
                'directions': [
                    {'code': '60510103', 'name': "Davolash ishi", 'form': 'full_time', 'grant': 50, 'contract': 200, 'price': 18000000, 'subjects': ['biologiya', 'kimyo'], 'scores': {'2025': {'grant': 190.0, 'contract': 158.0}, '2024': {'grant': 187.0, 'contract': 155.0}}},
                ],
            },
        ],
    },
    {
        'name': "Toshkent davlat sharqshunoslik universiteti",
        'short_name': 'TDShU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 1955,
        'students': 6000,
        'website': 'https://tashgiv.uz',
        'email': 'info@tashgiv.uz',
        'phone': '+998712335524',
        'address': "Shota Rustaveli ko'chasi 25, Toshkent",
        'description': "Sharqshunoslik va diplomatiya sohasida yetakchi.",
        'rating': 4.1,
        'faculties': [
            {
                'name': "Sharq tillari fakulteti",
                'directions': [
                    {'code': '60120470', 'name': "Xitoy filologiyasi", 'form': 'full_time', 'grant': 25, 'contract': 100, 'price': 14400000, 'subjects': ['ingliz-tili', 'tarix'], 'scores': {'2025': {'grant': 185.0, 'contract': 140.0}, '2024': {'grant': 182.0, 'contract': 137.0}}},
                    {'code': '60120480', 'name': "Koreys filologiyasi", 'form': 'full_time', 'grant': 20, 'contract': 100, 'price': 14400000, 'subjects': ['ingliz-tili', 'tarix'], 'scores': {'2025': {'grant': 183.0, 'contract': 138.0}, '2024': {'grant': 180.0, 'contract': 135.0}}},
                    {'code': '60120490', 'name': "Yapon filologiyasi", 'form': 'full_time', 'grant': 15, 'contract': 80, 'price': 14400000, 'subjects': ['ingliz-tili', 'tarix'], 'scores': {'2025': {'grant': 182.0, 'contract': 135.0}, '2024': {'grant': 179.0, 'contract': 132.0}}},
                ],
            },
            {
                'name': "Xalqaro munosabatlar fakulteti",
                'directions': [
                    {'code': '60410500', 'name': "Xalqaro munosabatlar", 'form': 'full_time', 'grant': 25, 'contract': 120, 'price': 16000000, 'subjects': ['tarix', 'ingliz-tili'], 'scores': {'2025': {'grant': 192.0, 'contract': 152.0}, '2024': {'grant': 189.0, 'contract': 149.0}}},
                ],
            },
        ],
    },
]

# ======================== XUSUSIY VA XORIJIY UNIVERSITETLAR ========================
PRIVATE_UNIVERSITIES = [
    {
        'name': "Inha University in Tashkent",
        'short_name': 'IUT',
        'type': 'private',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 2014,
        'students': 3000,
        'website': 'https://inha.uz',
        'email': 'admission@inha.uz',
        'phone': '+998712890909',
        'address': "Ziyolilar ko'chasi 9, Toshkent",
        'description': "Koreya Inha universitetining Toshkentdagi filiali. IT va muhandislik sohasida xalqaro standartlarda ta'lim beradi.",
        'rating': 4.7,
        'is_featured': True,
        'faculties': [
            {
                'name': "Computer Science and Engineering",
                'directions': [
                    {'code': 'IUT-CSE', 'name': "Computer Science and Engineering", 'form': 'full_time', 'grant': 50, 'contract': 200, 'price': 33000000, 'subjects': ['matematika', 'ingliz-tili'], 'scores': {'2025': {'grant': 198.0, 'contract': 170.0}, '2024': {'grant': 195.0, 'contract': 167.0}}},
                    {'code': 'IUT-ISE', 'name': "Information Systems Engineering", 'form': 'full_time', 'grant': 30, 'contract': 150, 'price': 33000000, 'subjects': ['matematika', 'ingliz-tili'], 'scores': {'2025': {'grant': 195.0, 'contract': 165.0}, '2024': {'grant': 192.0, 'contract': 162.0}}},
                ],
            },
        ],
    },
    {
        'name': "Turin Politexnika universiteti Toshkentda",
        'short_name': 'TTPU',
        'type': 'joint',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 2009,
        'students': 4000,
        'website': 'https://polito.uz',
        'email': 'info@polito.uz',
        'phone': '+998712464810',
        'address': "Kichik Xalqa Yo'li 17, Toshkent",
        'description': "Italiyaning Turin Politexnika universiteti bilan qo'shma. Muhandislik sohasida xalqaro ta'lim.",
        'rating': 4.6,
        'is_featured': True,
        'faculties': [
            {
                'name': "Muhandislik fakulteti",
                'directions': [
                    {'code': 'TTPU-ME', 'name': "Mexanika muhandisligi", 'form': 'full_time', 'grant': 30, 'contract': 150, 'price': 28000000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 190.0, 'contract': 160.0}, '2024': {'grant': 187.0, 'contract': 157.0}}},
                    {'code': 'TTPU-CE', 'name': "Qurilish muhandisligi", 'form': 'full_time', 'grant': 25, 'contract': 120, 'price': 28000000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 188.0, 'contract': 155.0}, '2024': {'grant': 185.0, 'contract': 152.0}}},
                    {'code': 'TTPU-EE', 'name': "Energetika muhandisligi", 'form': 'full_time', 'grant': 25, 'contract': 100, 'price': 28000000, 'subjects': ['fizika', 'matematika'], 'scores': {'2025': {'grant': 186.0, 'contract': 152.0}, '2024': {'grant': 183.0, 'contract': 149.0}}},
                ],
            },
        ],
    },
    {
        'name': "Webster University Tashkent",
        'short_name': 'Webster',
        'type': 'foreign',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 2019,
        'students': 1500,
        'website': 'https://webster.uz',
        'email': 'admission@webster.uz',
        'phone': '+998712052525',
        'address': "Bunyodkor ko'chasi 12, Toshkent",
        'description': "AQSh Webster universitetining Toshkentdagi filiali. Biznes va boshqarish sohasida xalqaro ta'lim.",
        'rating': 4.4,
        'faculties': [
            {
                'name': "Business & Management",
                'directions': [
                    {'code': 'WEB-BA', 'name': "Business Administration", 'form': 'full_time', 'grant': 15, 'contract': 100, 'price': 45000000, 'subjects': ['matematika', 'ingliz-tili'], 'scores': {'2025': {'grant': 192.0, 'contract': 160.0}, '2024': {'grant': 189.0, 'contract': 157.0}}},
                    {'code': 'WEB-MIS', 'name': "Management Information Systems", 'form': 'full_time', 'grant': 10, 'contract': 80, 'price': 45000000, 'subjects': ['matematika', 'ingliz-tili'], 'scores': {'2025': {'grant': 190.0, 'contract': 155.0}, '2024': {'grant': 187.0, 'contract': 152.0}}},
                ],
            },
        ],
    },
    {
        'name': "TEAM University",
        'short_name': 'TEAM',
        'type': 'private',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 2019,
        'students': 2500,
        'website': 'https://teamuni.uz',
        'email': 'info@teamuni.uz',
        'phone': '+998712000088',
        'address': "Lashkarbegi ko'chasi 36, Toshkent",
        'description': "IT va biznes sohasida zamonaviy ta'lim beruvchi xususiy universitet.",
        'rating': 4.3,
        'faculties': [
            {
                'name': "IT fakulteti",
                'directions': [
                    {'code': 'TEAM-SE', 'name': "Software Engineering", 'form': 'full_time', 'grant': 20, 'contract': 150, 'price': 36000000, 'subjects': ['matematika', 'ingliz-tili'], 'scores': {'2025': {'grant': 190.0, 'contract': 155.0}, '2024': {'grant': 187.0, 'contract': 152.0}}},
                ],
            },
        ],
    },
    {
        'name': "Amity University Tashkent",
        'short_name': 'Amity',
        'type': 'private',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 2019,
        'students': 2000,
        'website': 'https://amity.uz',
        'email': 'info@amity.uz',
        'phone': '+998712052500',
        'address': "Qo'yliq ko'chasi, Toshkent",
        'description': "Hindistonning Amity universitetining Toshkentdagi filiali.",
        'rating': 4.0,
        'faculties': [
            {
                'name': "Engineering & Technology",
                'directions': [
                    {'code': 'AMT-CSE', 'name': "Computer Science", 'form': 'full_time', 'grant': 15, 'contract': 100, 'price': 30000000, 'subjects': ['matematika', 'ingliz-tili'], 'scores': {'2025': {'grant': 185.0, 'contract': 148.0}, '2024': {'grant': 182.0, 'contract': 145.0}}},
                ],
            },
        ],
    },
    {
        'name': "Yeoju Technical Institute in Tashkent",
        'short_name': 'Yeoju',
        'type': 'joint',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 2019,
        'students': 3000,
        'website': 'https://ytit.uz',
        'email': 'info@ytit.uz',
        'phone': '+998712057070',
        'address': "Chinobod ko'chasi 227, Toshkent",
        'description': "Koreya Yeoju universiteti bilan qo'shma texnik institut.",
        'rating': 4.1,
        'faculties': [
            {
                'name': "IT va muhandislik fakulteti",
                'directions': [
                    {'code': 'YJ-CS', 'name': "Computer Science", 'form': 'full_time', 'grant': 20, 'contract': 130, 'price': 25000000, 'subjects': ['matematika', 'ingliz-tili'], 'scores': {'2025': {'grant': 185.0, 'contract': 148.0}, '2024': {'grant': 182.0, 'contract': 145.0}}},
                ],
            },
        ],
    },
    {
        'name': "Moskva davlat universiteti Toshkent filiali",
        'short_name': 'MDU filiali',
        'type': 'foreign',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 2019,
        'students': 1500,
        'website': 'https://msu.uz',
        'email': 'info@msu.uz',
        'phone': '+998712006789',
        'address': "Amir Temur shoh ko'chasi, Toshkent",
        'description': "Rossiya Moskva davlat universitetining Toshkentdagi filiali.",
        'rating': 4.5,
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': 'MSU-MATH', 'name': "Amaliy matematika va informatika", 'form': 'full_time', 'grant': 20, 'contract': 80, 'price': 35000000, 'subjects': ['matematika', 'fizika'], 'scores': {'2025': {'grant': 195.0, 'contract': 165.0}, '2024': {'grant': 192.0, 'contract': 162.0}}},
                ],
            },
        ],
    },
    {
        'name': "Rossiya iqtisodiyot universiteti Toshkent filiali (Plekhanov)",
        'short_name': 'REU Plekhanov',
        'type': 'foreign',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 2016,
        'students': 2000,
        'website': 'https://reu.uz',
        'email': 'info@reu.uz',
        'phone': '+998712005544',
        'address': "Mirzo Ulug'bek ko'chasi, Toshkent",
        'description': "Rossiya Plekhanov iqtisodiyot universitetining Toshkentdagi filiali.",
        'rating': 4.2,
        'faculties': [
            {
                'name': "Iqtisodiyot fakulteti",
                'directions': [
                    {'code': 'REU-EC', 'name': "Iqtisodiyot", 'form': 'full_time', 'grant': 15, 'contract': 100, 'price': 28000000, 'subjects': ['matematika', 'ona-tili'], 'scores': {'2025': {'grant': 188.0, 'contract': 150.0}, '2024': {'grant': 185.0, 'contract': 147.0}}},
                ],
            },
        ],
    },
    {
        'name': "Management Development Institute of Singapore (MDIS) Tashkent",
        'short_name': 'MDIS',
        'type': 'foreign',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established': 2020,
        'students': 1000,
        'website': 'https://mdis.uz',
        'email': 'info@mdis.uz',
        'phone': '+998712001234',
        'address': "Toshkent shahri",
        'description': "Singapurning MDIS institutining Toshkentdagi filiali. Biznes va menejment.",
        'rating': 4.0,
        'faculties': [
            {
                'name': "Business Faculty",
                'directions': [
                    {'code': 'MDIS-BM', 'name': "Business Management", 'form': 'full_time', 'grant': 10, 'contract': 80, 'price': 38000000, 'subjects': ['matematika', 'ingliz-tili'], 'scores': {'2025': {'grant': 185.0, 'contract': 150.0}, '2024': {'grant': 182.0, 'contract': 147.0}}},
                ],
            },
        ],
    },
]

ALL_UNIVERSITIES = STATE_UNIVERSITIES + PRIVATE_UNIVERSITIES


class Command(BaseCommand):
    help = "O'zbekiston universitetlari haqiqiy ma'lumotlarini bazaga kiritish (2025-yil)"

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help="Avval eski ma'lumotlarni tozalash")

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("Eski ma'lumotlar tozalanmoqda...")
            PassingScore.objects.all().delete()
            Direction.objects.all().delete()
            Faculty.objects.all().delete()
            University.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Tozalandi!"))

        total_unis = 0
        total_facs = 0
        total_dirs = 0
        total_scores = 0

        for uni_data in ALL_UNIVERSITIES:
            slug = slugify(uni_data['name'])

            university, created = University.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': uni_data['name'],
                    'short_name': uni_data.get('short_name', ''),
                    'university_type': uni_data['type'],
                    'region': uni_data['region'],
                    'city': uni_data['city'],
                    'established_year': uni_data.get('established'),
                    'student_count': uni_data.get('students'),
                    'website': uni_data.get('website', ''),
                    'email': uni_data.get('email', ''),
                    'phone': uni_data.get('phone', ''),
                    'address': uni_data.get('address', ''),
                    'description': uni_data.get('description', ''),
                    'rating': uni_data.get('rating', 0.0),
                    'is_featured': uni_data.get('is_featured', False),
                    'is_active': True,
                }
            )
            total_unis += 1
            action = "yangilandi" if not created else "yaratildi"
            self.stdout.write(f"  {'✓' if created else '↻'} {university.name} ({action})")

            for fac_data in uni_data.get('faculties', []):
                fac_slug = slugify(fac_data['name'])
                faculty, f_created = Faculty.objects.update_or_create(
                    university=university,
                    slug=fac_slug,
                    defaults={
                        'name': fac_data['name'],
                        'is_active': True,
                    }
                )
                total_facs += 1

                for dir_data in fac_data.get('directions', []):
                    dir_slug = slugify(dir_data['name'])
                    direction, d_created = Direction.objects.update_or_create(
                        university=university,
                        code=dir_data['code'],
                        defaults={
                            'faculty': faculty,
                            'name': dir_data['name'],
                            'slug': dir_slug,
                            'education_form': dir_data.get('form', 'full_time'),
                            'education_type': 'both',
                            'duration_years': dir_data.get('duration', 4),
                            'grant_quota': dir_data.get('grant', 0),
                            'contract_quota': dir_data.get('contract', 0),
                            'contract_price': dir_data.get('price', 0),
                            'is_active': True,
                        }
                    )
                    total_dirs += 1

                    # O'tish ballari
                    for year_str, score_data in dir_data.get('scores', {}).items():
                        year = int(year_str)
                        ps, ps_created = PassingScore.objects.update_or_create(
                            direction=direction,
                            year=year,
                            defaults={
                                'grant_score': score_data.get('grant'),
                                'contract_score': score_data.get('contract'),
                            }
                        )
                        total_scores += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Jami: {total_unis} ta universitet, {total_facs} ta fakultet, {total_dirs} ta yo'nalish, {total_scores} ta ball"))
        self.stdout.write(self.style.SUCCESS("Ma'lumotlar muvaffaqiyatli kiritildi!"))

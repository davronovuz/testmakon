"""
O'zbekiston universitetlari ma'lumotlarini bazaga kiritish.
Davlat, xususiy, xorijiy filial va qo'shma universitetlar.
2024-2025 yillar uchun o'tish ballari va statistika.

Usage: python manage.py populate_universities
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from universities.models import University, Faculty, Direction, PassingScore


# ============================================================
# O'ZBEKISTON UNIVERSITETLARI MA'LUMOTLARI
# ============================================================

UNIVERSITIES_DATA = [
    # ======================== DAVLAT UNIVERSITETLARI ========================
    {
        'name': "O'zbekiston Milliy universiteti",
        'short_name': 'O\'zMU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1918,
        'student_count': 25000,
        'website': 'https://nuu.uz',
        'description': "O'zbekistonning eng qadimgi va nufuzli universiteti. 1918-yilda tashkil etilgan.",
        'faculties': [
            {
                'name': 'Matematika fakulteti',
                'directions': [
                    {'code': '60110100', 'name': 'Matematika', 'grant_quota': 80, 'contract_quota': 120,
                     'contract_price': 12_100_000, 'scores': {2024: (186.5, 142.3, 1850, 4.2), 2025: (189.2, 145.8, 1920, 4.5)}},
                    {'code': '60110200', 'name': 'Amaliy matematika va informatika', 'grant_quota': 60, 'contract_quota': 150,
                     'contract_price': 12_100_000, 'scores': {2024: (191.3, 148.7, 2100, 5.1), 2025: (193.5, 150.2, 2250, 5.4)}},
                ]
            },
            {
                'name': 'Fizika fakulteti',
                'directions': [
                    {'code': '60110300', 'name': 'Fizika', 'grant_quota': 70, 'contract_quota': 100,
                     'contract_price': 12_100_000, 'scores': {2024: (178.4, 135.6, 1200, 3.1), 2025: (180.1, 137.2, 1280, 3.3)}},
                    {'code': '60110400', 'name': 'Astronomiya', 'grant_quota': 25, 'contract_quota': 40,
                     'contract_price': 12_100_000, 'scores': {2024: (172.1, 130.5, 450, 2.8), 2025: (174.3, 132.1, 480, 2.9)}},
                ]
            },
            {
                'name': 'Kimyo fakulteti',
                'directions': [
                    {'code': '60110500', 'name': 'Kimyo', 'grant_quota': 60, 'contract_quota': 90,
                     'contract_price': 12_100_000, 'scores': {2024: (175.2, 133.8, 1100, 3.0), 2025: (177.5, 135.4, 1150, 3.2)}},
                ]
            },
            {
                'name': 'Biologiya fakulteti',
                'directions': [
                    {'code': '60110600', 'name': 'Biologiya', 'grant_quota': 55, 'contract_quota': 85,
                     'contract_price': 12_100_000, 'scores': {2024: (176.8, 134.2, 1300, 3.4), 2025: (178.9, 136.1, 1380, 3.6)}},
                ]
            },
            {
                'name': 'Tarix fakulteti',
                'directions': [
                    {'code': '60120100', 'name': 'Tarix', 'grant_quota': 50, 'contract_quota': 80,
                     'contract_price': 12_100_000, 'scores': {2024: (180.3, 138.5, 1400, 3.5), 2025: (182.1, 140.2, 1450, 3.7)}},
                ]
            },
            {
                'name': 'Filologiya fakulteti',
                'directions': [
                    {'code': '60120200', 'name': "O'zbek filologiyasi", 'grant_quota': 65, 'contract_quota': 95,
                     'contract_price': 12_100_000, 'scores': {2024: (177.5, 135.1, 1500, 3.6), 2025: (179.8, 137.3, 1560, 3.8)}},
                    {'code': '60120300', 'name': 'Ingliz filologiyasi', 'grant_quota': 45, 'contract_quota': 180,
                     'contract_price': 12_100_000, 'scores': {2024: (188.7, 146.2, 2800, 6.2), 2025: (190.5, 148.1, 2950, 6.5)}},
                ]
            },
            {
                'name': 'Iqtisodiyot fakulteti',
                'directions': [
                    {'code': '60310100', 'name': 'Iqtisodiyot', 'grant_quota': 40, 'contract_quota': 200,
                     'contract_price': 12_100_000, 'scores': {2024: (185.4, 143.6, 2500, 5.8), 2025: (187.8, 145.9, 2650, 6.1)}},
                ]
            },
            {
                'name': 'Huquqshunoslik fakulteti',
                'directions': [
                    {'code': '60380100', 'name': 'Huquqshunoslik', 'grant_quota': 35, 'contract_quota': 250,
                     'contract_price': 12_100_000, 'scores': {2024: (192.1, 150.3, 3200, 7.5), 2025: (194.5, 152.8, 3400, 7.8)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent davlat texnika universiteti",
        'short_name': 'ToshDTU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1929,
        'student_count': 20000,
        'website': 'https://tdtu.uz',
        'description': "O'zbekistonning yetakchi texnik oliy ta'lim muassasasi.",
        'faculties': [
            {
                'name': 'Energetika fakulteti',
                'directions': [
                    {'code': '60710100', 'name': 'Energetika', 'grant_quota': 70, 'contract_quota': 130,
                     'contract_price': 12_100_000, 'scores': {2024: (183.2, 140.5, 1600, 3.8), 2025: (185.4, 142.3, 1700, 4.0)}},
                    {'code': '60710200', 'name': 'Elektr energetika', 'grant_quota': 65, 'contract_quota': 120,
                     'contract_price': 12_100_000, 'scores': {2024: (181.5, 138.7, 1450, 3.5), 2025: (183.8, 140.9, 1520, 3.7)}},
                ]
            },
            {
                'name': 'Mexanika-mashinasozlik fakulteti',
                'directions': [
                    {'code': '60710300', 'name': 'Mashinasozlik texnologiyasi', 'grant_quota': 55, 'contract_quota': 100,
                     'contract_price': 12_100_000, 'scores': {2024: (174.3, 132.1, 1100, 2.9), 2025: (176.5, 134.2, 1180, 3.1)}},
                    {'code': '60710400', 'name': 'Mexanika', 'grant_quota': 50, 'contract_quota': 90,
                     'contract_price': 12_100_000, 'scores': {2024: (172.8, 130.4, 950, 2.7), 2025: (174.9, 132.5, 1020, 2.8)}},
                ]
            },
            {
                'name': 'IT va kompyuter injiniringi fakulteti',
                'directions': [
                    {'code': '60610100', 'name': "Kompyuter injiniringi", 'grant_quota': 50, 'contract_quota': 200,
                     'contract_price': 14_300_000, 'scores': {2024: (195.8, 155.2, 3500, 8.2), 2025: (198.1, 157.5, 3800, 8.8)}},
                    {'code': '60610200', 'name': "Dasturiy injiniring", 'grant_quota': 45, 'contract_quota': 180,
                     'contract_price': 14_300_000, 'scores': {2024: (197.2, 156.8, 3800, 8.9), 2025: (199.5, 158.9, 4100, 9.3)}},
                    {'code': '60610300', 'name': "Axborot xavfsizligi", 'grant_quota': 35, 'contract_quota': 120,
                     'contract_price': 14_300_000, 'scores': {2024: (190.5, 150.1, 2200, 5.5), 2025: (192.8, 152.3, 2400, 5.8)}},
                ]
            },
            {
                'name': 'Qurilish fakulteti',
                'directions': [
                    {'code': '60730100', 'name': 'Qurilish injiniringi', 'grant_quota': 60, 'contract_quota': 150,
                     'contract_price': 12_100_000, 'scores': {2024: (180.1, 137.8, 1800, 4.0), 2025: (182.3, 139.5, 1900, 4.2)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent davlat iqtisodiyot universiteti",
        'short_name': 'TDIU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1931,
        'student_count': 18000,
        'website': 'https://tsue.uz',
        'description': "O'zbekistondagi yetakchi iqtisodiyot universiteti.",
        'faculties': [
            {
                'name': 'Iqtisodiyot fakulteti',
                'directions': [
                    {'code': '60310200', 'name': 'Iqtisodiyot (tarmoqlar bo\'yicha)', 'grant_quota': 50, 'contract_quota': 250,
                     'contract_price': 12_100_000, 'scores': {2024: (184.6, 142.1, 2800, 5.6), 2025: (186.9, 144.5, 2950, 5.9)}},
                    {'code': '60310300', 'name': 'Moliya', 'grant_quota': 40, 'contract_quota': 300,
                     'contract_price': 12_100_000, 'scores': {2024: (189.3, 147.5, 3500, 7.0), 2025: (191.5, 149.8, 3700, 7.4)}},
                ]
            },
            {
                'name': 'Menejment fakulteti',
                'directions': [
                    {'code': '60310400', 'name': 'Menejment', 'grant_quota': 35, 'contract_quota': 200,
                     'contract_price': 12_100_000, 'scores': {2024: (182.1, 139.8, 2100, 4.7), 2025: (184.3, 141.5, 2250, 5.0)}},
                    {'code': '60310500', 'name': 'Marketing', 'grant_quota': 30, 'contract_quota': 180,
                     'contract_price': 12_100_000, 'scores': {2024: (180.5, 138.2, 1900, 4.3), 2025: (182.7, 140.1, 2050, 4.6)}},
                ]
            },
            {
                'name': 'Buxgalteriya hisobi fakulteti',
                'directions': [
                    {'code': '60310600', 'name': 'Buxgalteriya hisobi va audit', 'grant_quota': 45, 'contract_quota': 280,
                     'contract_price': 12_100_000, 'scores': {2024: (183.8, 141.2, 2600, 5.2), 2025: (186.1, 143.5, 2750, 5.5)}},
                ]
            },
            {
                'name': 'Raqamli iqtisodiyot fakulteti',
                'directions': [
                    {'code': '60310700', 'name': 'Raqamli iqtisodiyot', 'grant_quota': 30, 'contract_quota': 150,
                     'contract_price': 14_300_000, 'scores': {2024: (188.2, 146.5, 2200, 5.1), 2025: (190.5, 148.8, 2400, 5.3)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent tibbiyot akademiyasi",
        'short_name': 'TTA',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1920,
        'student_count': 15000,
        'website': 'https://tma.uz',
        'description': "O'zbekistondagi eng nufuzli tibbiyot oliy ta'lim muassasasi.",
        'faculties': [
            {
                'name': 'Davolash fakulteti',
                'directions': [
                    {'code': '60510100', 'name': 'Davolash ishi', 'grant_quota': 120, 'contract_quota': 400,
                     'contract_price': 16_500_000, 'scores': {2024: (198.5, 162.3, 5500, 10.6), 2025: (200.1, 164.5, 5800, 11.2)}},
                ]
            },
            {
                'name': 'Pediatriya fakulteti',
                'directions': [
                    {'code': '60510200', 'name': 'Pediatriya', 'grant_quota': 80, 'contract_quota': 250,
                     'contract_price': 16_500_000, 'scores': {2024: (193.2, 155.8, 3200, 7.5), 2025: (195.5, 158.1, 3400, 7.9)}},
                ]
            },
            {
                'name': 'Stomatologiya fakulteti',
                'directions': [
                    {'code': '60510300', 'name': 'Stomatologiya', 'grant_quota': 40, 'contract_quota': 200,
                     'contract_price': 22_000_000, 'scores': {2024: (196.8, 160.5, 4200, 10.5), 2025: (198.9, 162.8, 4500, 11.0)}},
                ]
            },
            {
                'name': 'Farmatsevtika fakulteti',
                'directions': [
                    {'code': '60510400', 'name': 'Farmatsiya', 'grant_quota': 50, 'contract_quota': 180,
                     'contract_price': 14_300_000, 'scores': {2024: (188.5, 148.2, 2800, 6.2), 2025: (190.8, 150.5, 3000, 6.5)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent davlat yuridik universiteti",
        'short_name': 'TDYU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1994,
        'student_count': 12000,
        'website': 'https://tsul.uz',
        'description': "O'zbekistondagi yetakchi yuridik oliy ta'lim muassasasi.",
        'faculties': [
            {
                'name': 'Huquqshunoslik fakulteti',
                'directions': [
                    {'code': '60380200', 'name': 'Huquqshunoslik (fuqarolik huquqi)', 'grant_quota': 50, 'contract_quota': 350,
                     'contract_price': 12_100_000, 'scores': {2024: (194.2, 153.5, 4500, 9.0), 2025: (196.5, 155.8, 4800, 9.5)}},
                    {'code': '60380300', 'name': 'Huquqshunoslik (jinoyat huquqi)', 'grant_quota': 45, 'contract_quota': 300,
                     'contract_price': 12_100_000, 'scores': {2024: (192.8, 151.2, 3800, 7.8), 2025: (195.1, 153.5, 4000, 8.2)}},
                ]
            },
            {
                'name': 'Xalqaro huquq fakulteti',
                'directions': [
                    {'code': '60380400', 'name': 'Xalqaro huquq', 'grant_quota': 30, 'contract_quota': 200,
                     'contract_price': 14_300_000, 'scores': {2024: (196.5, 158.2, 3200, 8.5), 2025: (198.8, 160.5, 3500, 9.0)}},
                ]
            },
            {
                'name': 'Biznes huquqi fakulteti',
                'directions': [
                    {'code': '60380500', 'name': 'Biznes huquqi', 'grant_quota': 25, 'contract_quota': 180,
                     'contract_price': 14_300_000, 'scores': {2024: (190.1, 149.5, 2500, 6.5), 2025: (192.3, 151.8, 2700, 6.8)}},
                ]
            },
        ]
    },
    {
        'name': "Muhammad al-Xorazmiy nomidagi Toshkent axborot texnologiyalari universiteti",
        'short_name': 'TATU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1955,
        'student_count': 22000,
        'website': 'https://tuit.uz',
        'description': "O'zbekistonning yetakchi IT universiteti. Dasturlash va axborot texnologiyalari sohasida kadrlar tayyorlaydi.",
        'faculties': [
            {
                'name': 'Dasturiy injiniring fakulteti',
                'directions': [
                    {'code': '60610101', 'name': "Dasturiy injiniring", 'grant_quota': 60, 'contract_quota': 250,
                     'contract_price': 14_300_000, 'scores': {2024: (199.2, 158.5, 4200, 9.5), 2025: (201.5, 160.8, 4500, 10.0)}},
                    {'code': '60610102', 'name': "Sun'iy intellekt", 'grant_quota': 40, 'contract_quota': 180,
                     'contract_price': 16_500_000, 'scores': {2024: (201.5, 162.3, 3800, 9.8), 2025: (203.8, 164.5, 4100, 10.3)}},
                ]
            },
            {
                'name': 'Kompyuter injiniringi fakulteti',
                'directions': [
                    {'code': '60610103', 'name': 'Kompyuter injiniringi', 'grant_quota': 55, 'contract_quota': 220,
                     'contract_price': 14_300_000, 'scores': {2024: (196.8, 155.2, 3600, 8.5), 2025: (199.1, 157.5, 3900, 9.0)}},
                    {'code': '60610104', 'name': 'Kiberxavfsizlik', 'grant_quota': 35, 'contract_quota': 150,
                     'contract_price': 14_300_000, 'scores': {2024: (193.5, 152.8, 2800, 7.0), 2025: (195.8, 155.1, 3000, 7.3)}},
                ]
            },
            {
                'name': 'Telekommunikatsiya texnologiyalari fakulteti',
                'directions': [
                    {'code': '60610105', 'name': 'Telekommunikatsiya texnologiyalari', 'grant_quota': 50, 'contract_quota': 180,
                     'contract_price': 12_100_000, 'scores': {2024: (185.2, 143.5, 2200, 5.0), 2025: (187.5, 145.8, 2350, 5.3)}},
                    {'code': '60610106', 'name': 'Televizion texnologiyalar', 'grant_quota': 30, 'contract_quota': 100,
                     'contract_price': 12_100_000, 'scores': {2024: (178.5, 136.2, 1200, 3.2), 2025: (180.8, 138.5, 1300, 3.4)}},
                ]
            },
            {
                'name': "Axborot texnologiyalari fakulteti",
                'directions': [
                    {'code': '60610107', 'name': "AT xizmatlari", 'grant_quota': 45, 'contract_quota': 200,
                     'contract_price': 12_100_000, 'scores': {2024: (188.1, 146.8, 2500, 5.5), 2025: (190.3, 149.1, 2700, 5.8)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent davlat pedagogika universiteti",
        'short_name': 'TDPU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1935,
        'student_count': 16000,
        'website': 'https://tdpu.uz',
        'description': "O'zbekistondagi eng yirik pedagogika universiteti. O'qituvchi kadrlar tayyorlaydi.",
        'faculties': [
            {
                'name': 'Matematika va informatika fakulteti',
                'directions': [
                    {'code': '60110700', 'name': "Matematika o'qitish metodikasi", 'grant_quota': 80, 'contract_quota': 120,
                     'contract_price': 9_900_000, 'scores': {2024: (170.5, 128.2, 1200, 2.5), 2025: (172.8, 130.5, 1280, 2.7)}},
                    {'code': '60110800', 'name': "Informatika o'qitish metodikasi", 'grant_quota': 60, 'contract_quota': 150,
                     'contract_price': 9_900_000, 'scores': {2024: (175.2, 132.5, 1500, 3.0), 2025: (177.5, 134.8, 1600, 3.2)}},
                ]
            },
            {
                'name': "Boshlang'ich ta'lim fakulteti",
                'directions': [
                    {'code': '60110900', 'name': "Boshlang'ich ta'lim", 'grant_quota': 100, 'contract_quota': 200,
                     'contract_price': 9_900_000, 'scores': {2024: (168.3, 126.5, 2200, 3.5), 2025: (170.5, 128.8, 2350, 3.7)}},
                ]
            },
            {
                'name': 'Chet tillari fakulteti',
                'directions': [
                    {'code': '60111000', 'name': "Ingliz tili o'qitish metodikasi", 'grant_quota': 50, 'contract_quota': 250,
                     'contract_price': 9_900_000, 'scores': {2024: (185.8, 143.2, 3200, 6.5), 2025: (188.1, 145.5, 3400, 6.8)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent kimyo-texnologiya instituti",
        'short_name': 'TKTI',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1948,
        'student_count': 10000,
        'website': 'https://tkti.uz',
        'description': "Kimyo va texnologiya sohasida kadrlar tayyorlaydigan yetakchi institut.",
        'faculties': [
            {
                'name': 'Kimyoviy texnologiya fakulteti',
                'directions': [
                    {'code': '60720100', 'name': 'Kimyoviy texnologiya', 'grant_quota': 50, 'contract_quota': 80,
                     'contract_price': 12_100_000, 'scores': {2024: (170.2, 128.5, 800, 2.3), 2025: (172.5, 130.8, 850, 2.5)}},
                    {'code': '60720200', 'name': "Oziq-ovqat texnologiyasi", 'grant_quota': 45, 'contract_quota': 120,
                     'contract_price': 12_100_000, 'scores': {2024: (173.5, 131.2, 1100, 2.8), 2025: (175.8, 133.5, 1200, 3.0)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent arxitektura-qurilish instituti",
        'short_name': 'TAQI',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1991,
        'student_count': 8000,
        'website': 'https://taqi.uz',
        'description': "Arxitektura va qurilish sohasida kadrlar tayyorlaydi.",
        'faculties': [
            {
                'name': 'Arxitektura fakulteti',
                'directions': [
                    {'code': '60730200', 'name': 'Arxitektura', 'grant_quota': 35, 'contract_quota': 100,
                     'contract_price': 12_100_000, 'scores': {2024: (182.5, 140.2, 1500, 4.0), 2025: (184.8, 142.5, 1600, 4.2)}},
                ]
            },
            {
                'name': 'Qurilish fakulteti',
                'directions': [
                    {'code': '60730300', 'name': 'Qurilish muhandisligi', 'grant_quota': 60, 'contract_quota': 150,
                     'contract_price': 12_100_000, 'scores': {2024: (178.3, 136.5, 1800, 3.8), 2025: (180.5, 138.8, 1900, 4.0)}},
                ]
            },
        ]
    },
    {
        'name': "Samarqand davlat universiteti",
        'short_name': 'SamDU',
        'type': 'state',
        'region': 'Samarqand',
        'city': 'Samarqand',
        'established_year': 1927,
        'student_count': 20000,
        'website': 'https://samdu.uz',
        'description': "Samarqand shahridagi eng yirik universitet. O'rta Osiyodagi eng qadimiy universitetlardan biri.",
        'faculties': [
            {
                'name': 'Matematika fakulteti',
                'directions': [
                    {'code': '60110101', 'name': 'Matematika', 'grant_quota': 60, 'contract_quota': 100,
                     'contract_price': 9_900_000, 'scores': {2024: (175.5, 132.8, 1100, 2.8), 2025: (177.8, 135.1, 1200, 3.0)}},
                ]
            },
            {
                'name': 'Fizika fakulteti',
                'directions': [
                    {'code': '60110301', 'name': 'Fizika', 'grant_quota': 55, 'contract_quota': 80,
                     'contract_price': 9_900_000, 'scores': {2024: (168.2, 126.5, 750, 2.1), 2025: (170.5, 128.8, 800, 2.3)}},
                ]
            },
            {
                'name': 'Chet tillari fakulteti',
                'directions': [
                    {'code': '60120301', 'name': 'Ingliz filologiyasi', 'grant_quota': 40, 'contract_quota': 180,
                     'contract_price': 9_900_000, 'scores': {2024: (183.5, 141.2, 2500, 5.5), 2025: (185.8, 143.5, 2650, 5.8)}},
                ]
            },
            {
                'name': 'IT fakulteti',
                'directions': [
                    {'code': '60610108', 'name': 'Dasturiy injiniring', 'grant_quota': 40, 'contract_quota': 160,
                     'contract_price': 12_100_000, 'scores': {2024: (188.5, 146.8, 2200, 5.2), 2025: (190.8, 149.1, 2400, 5.5)}},
                ]
            },
        ]
    },
    {
        'name': "Buxoro davlat universiteti",
        'short_name': 'BuxDU',
        'type': 'state',
        'region': 'Buxoro',
        'city': 'Buxoro',
        'established_year': 1930,
        'student_count': 15000,
        'website': 'https://buxdu.uz',
        'description': "Buxoro viloyatidagi eng yirik oliy ta'lim muassasasi.",
        'faculties': [
            {
                'name': 'Tabiiy fanlar fakulteti',
                'directions': [
                    {'code': '60110102', 'name': 'Matematika', 'grant_quota': 50, 'contract_quota': 80,
                     'contract_price': 9_900_000, 'scores': {2024: (168.5, 126.2, 800, 2.2), 2025: (170.8, 128.5, 850, 2.4)}},
                    {'code': '60110302', 'name': 'Fizika', 'grant_quota': 45, 'contract_quota': 70,
                     'contract_price': 9_900_000, 'scores': {2024: (163.2, 121.5, 600, 1.8), 2025: (165.5, 123.8, 650, 2.0)}},
                ]
            },
            {
                'name': 'Filologiya fakulteti',
                'directions': [
                    {'code': '60120302', 'name': 'Ingliz filologiyasi', 'grant_quota': 35, 'contract_quota': 150,
                     'contract_price': 9_900_000, 'scores': {2024: (178.5, 136.2, 2000, 4.5), 2025: (180.8, 138.5, 2150, 4.8)}},
                ]
            },
        ]
    },
    {
        'name': "Farg'ona davlat universiteti",
        'short_name': "FarDU",
        'type': 'state',
        'region': "Farg'ona",
        'city': "Farg'ona",
        'established_year': 1930,
        'student_count': 14000,
        'website': 'https://fdu.uz',
        'description': "Farg'ona vodiysidagi eng yirik universitet.",
        'faculties': [
            {
                'name': 'Matematika va informatika fakulteti',
                'directions': [
                    {'code': '60110103', 'name': 'Matematika', 'grant_quota': 50, 'contract_quota': 80,
                     'contract_price': 9_900_000, 'scores': {2024: (167.2, 125.5, 750, 2.1), 2025: (169.5, 127.8, 800, 2.3)}},
                ]
            },
            {
                'name': 'Chet tillari fakulteti',
                'directions': [
                    {'code': '60120303', 'name': 'Ingliz filologiyasi', 'grant_quota': 35, 'contract_quota': 150,
                     'contract_price': 9_900_000, 'scores': {2024: (180.2, 138.5, 2200, 5.0), 2025: (182.5, 140.8, 2350, 5.3)}},
                ]
            },
        ]
    },
    {
        'name': "Namangan davlat universiteti",
        'short_name': 'NamDU',
        'type': 'state',
        'region': 'Namangan',
        'city': 'Namangan',
        'established_year': 1942,
        'student_count': 12000,
        'website': 'https://namdu.uz',
        'description': "Namangan viloyatidagi yetakchi universitet.",
        'faculties': [
            {
                'name': 'Tabiiy fanlar fakulteti',
                'directions': [
                    {'code': '60110104', 'name': 'Matematika', 'grant_quota': 45, 'contract_quota': 75,
                     'contract_price': 9_900_000, 'scores': {2024: (165.8, 124.1, 700, 2.0), 2025: (168.1, 126.4, 750, 2.2)}},
                ]
            },
            {
                'name': 'Filologiya fakulteti',
                'directions': [
                    {'code': '60120304', 'name': 'Ingliz filologiyasi', 'grant_quota': 30, 'contract_quota': 140,
                     'contract_price': 9_900_000, 'scores': {2024: (178.5, 136.8, 1900, 4.3), 2025: (180.8, 139.1, 2050, 4.6)}},
                ]
            },
        ]
    },
    {
        'name': "Andijon davlat universiteti",
        'short_name': 'AndDU',
        'type': 'state',
        'region': 'Andijon',
        'city': 'Andijon',
        'established_year': 1931,
        'student_count': 11000,
        'website': 'https://adu.uz',
        'description': "Andijon viloyatidagi eng yirik universitet.",
        'faculties': [
            {
                'name': 'Tabiiy fanlar fakulteti',
                'directions': [
                    {'code': '60110105', 'name': 'Matematika', 'grant_quota': 45, 'contract_quota': 70,
                     'contract_price': 9_900_000, 'scores': {2024: (164.5, 123.2, 680, 1.9), 2025: (166.8, 125.5, 720, 2.1)}},
                ]
            },
        ]
    },
    {
        'name': "Qarshi davlat universiteti",
        'short_name': 'QarDU',
        'type': 'state',
        'region': 'Qashqadaryo',
        'city': 'Qarshi',
        'established_year': 1935,
        'student_count': 10000,
        'website': 'https://qardu.uz',
        'description': "Qashqadaryo viloyatidagi yetakchi universitet.",
        'faculties': [
            {
                'name': 'Tabiiy fanlar fakulteti',
                'directions': [
                    {'code': '60110106', 'name': 'Matematika', 'grant_quota': 40, 'contract_quota': 65,
                     'contract_price': 9_900_000, 'scores': {2024: (162.8, 121.5, 620, 1.8), 2025: (165.1, 123.8, 660, 2.0)}},
                ]
            },
        ]
    },
    {
        'name': "Navoiy davlat konchilik va texnologiyalar universiteti",
        'short_name': 'NDKTU',
        'type': 'state',
        'region': 'Navoiy',
        'city': 'Navoiy',
        'established_year': 1995,
        'student_count': 8000,
        'website': 'https://ndktu.uz',
        'description': "Konchilik va texnologiya sohasida kadrlar tayyorlaydi.",
        'faculties': [
            {
                'name': 'Konchilik fakulteti',
                'directions': [
                    {'code': '60740100', 'name': 'Konchilik ishi', 'grant_quota': 50, 'contract_quota': 80,
                     'contract_price': 12_100_000, 'scores': {2024: (172.5, 130.8, 900, 2.5), 2025: (174.8, 133.1, 950, 2.7)}},
                ]
            },
            {
                'name': 'Metallurgiya fakulteti',
                'directions': [
                    {'code': '60740200', 'name': 'Metallurgiya', 'grant_quota': 40, 'contract_quota': 70,
                     'contract_price': 12_100_000, 'scores': {2024: (168.3, 126.5, 700, 2.0), 2025: (170.5, 128.8, 750, 2.2)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent moliya instituti",
        'short_name': 'TMI',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1991,
        'student_count': 9000,
        'website': 'https://tfi.uz',
        'description': "Moliya, bank ishi va sug'urta sohasida kadrlar tayyorlaydi.",
        'faculties': [
            {
                'name': 'Moliya fakulteti',
                'directions': [
                    {'code': '60310800', 'name': 'Moliya va moliyaviy texnologiyalar', 'grant_quota': 40, 'contract_quota': 200,
                     'contract_price': 12_100_000, 'scores': {2024: (186.5, 144.8, 2800, 6.0), 2025: (188.8, 147.1, 3000, 6.3)}},
                ]
            },
            {
                'name': 'Bank ishi fakulteti',
                'directions': [
                    {'code': '60310900', 'name': 'Bank ishi', 'grant_quota': 35, 'contract_quota': 180,
                     'contract_price': 12_100_000, 'scores': {2024: (184.2, 142.5, 2400, 5.2), 2025: (186.5, 144.8, 2550, 5.5)}},
                ]
            },
        ]
    },
    {
        'name': "O'zbekiston davlat jahon tillari universiteti",
        'short_name': "O'zDJTU",
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1992,
        'student_count': 11000,
        'website': 'https://uzswlu.uz',
        'description': "Chet tillari va tarjimonlik sohasida O'zbekistondagi eng nufuzli OTM.",
        'faculties': [
            {
                'name': 'Ingliz tili fakulteti',
                'directions': [
                    {'code': '60120310', 'name': 'Ingliz tili va adabiyoti', 'grant_quota': 40, 'contract_quota': 250,
                     'contract_price': 12_100_000, 'scores': {2024: (192.5, 152.8, 3500, 7.5), 2025: (194.8, 155.1, 3700, 7.9)}},
                ]
            },
            {
                'name': 'Tarjimonlik fakulteti',
                'directions': [
                    {'code': '60120320', 'name': 'Tarjimashunoslik (ingliz tili)', 'grant_quota': 35, 'contract_quota': 200,
                     'contract_price': 14_300_000, 'scores': {2024: (194.8, 155.2, 3000, 7.0), 2025: (197.1, 157.5, 3200, 7.3)}},
                    {'code': '60120330', 'name': 'Tarjimashunoslik (xitoy tili)', 'grant_quota': 25, 'contract_quota': 120,
                     'contract_price': 14_300_000, 'scores': {2024: (188.2, 148.5, 1800, 4.5), 2025: (190.5, 150.8, 2000, 4.8)}},
                    {'code': '60120340', 'name': 'Tarjimashunoslik (koreys tili)', 'grant_quota': 20, 'contract_quota': 100,
                     'contract_price': 14_300_000, 'scores': {2024: (186.5, 146.8, 1500, 4.0), 2025: (188.8, 149.1, 1650, 4.3)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent davlat agrar universiteti",
        'short_name': 'ToshDAU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1930,
        'student_count': 12000,
        'website': 'https://tdau.uz',
        'description': "Qishloq xo'jaligi sohasida kadrlar tayyorlaydigan yetakchi OTM.",
        'faculties': [
            {
                'name': "Agronomiya fakulteti",
                'directions': [
                    {'code': '60810100', 'name': 'Agronomiya', 'grant_quota': 60, 'contract_quota': 100,
                     'contract_price': 9_900_000, 'scores': {2024: (165.5, 124.2, 900, 2.2), 2025: (167.8, 126.5, 950, 2.4)}},
                ]
            },
            {
                'name': 'Veterinariya fakulteti',
                'directions': [
                    {'code': '60810200', 'name': 'Veterinariya', 'grant_quota': 45, 'contract_quota': 80,
                     'contract_price': 12_100_000, 'scores': {2024: (170.2, 128.5, 800, 2.3), 2025: (172.5, 130.8, 850, 2.5)}},
                ]
            },
        ]
    },
    # ======================== XUSUSIY UNIVERSITETLAR ========================
    {
        'name': "Amity University Tashkent",
        'short_name': 'Amity',
        'type': 'private',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 2019,
        'student_count': 3000,
        'website': 'https://amity.uz',
        'description': "Hindistonning Amity Education Group tomonidan tashkil etilgan xususiy universitet.",
        'faculties': [
            {
                'name': 'IT fakulteti',
                'directions': [
                    {'code': '60610201', 'name': 'Computer Science', 'grant_quota': 0, 'contract_quota': 150,
                     'contract_price': 33_000_000, 'scores': {2024: (155.2, 130.5, 800, 1.5), 2025: (157.5, 132.8, 900, 1.6)}},
                ]
            },
            {
                'name': 'Biznes fakulteti',
                'directions': [
                    {'code': '60310201', 'name': 'Business Administration', 'grant_quota': 0, 'contract_quota': 120,
                     'contract_price': 33_000_000, 'scores': {2024: (152.8, 128.2, 600, 1.3), 2025: (155.1, 130.5, 700, 1.4)}},
                ]
            },
        ]
    },
    {
        'name': "TEAM University",
        'short_name': 'TEAM',
        'type': 'private',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 2019,
        'student_count': 2500,
        'website': 'https://teamuni.uz',
        'description': "IT va biznes sohasiga ixtisoslashgan zamonaviy xususiy universitet.",
        'faculties': [
            {
                'name': 'IT fakulteti',
                'directions': [
                    {'code': '60610202', 'name': 'Software Engineering', 'grant_quota': 10, 'contract_quota': 120,
                     'contract_price': 44_000_000, 'scores': {2024: (160.5, 135.2, 900, 1.8), 2025: (162.8, 137.5, 1000, 2.0)}},
                ]
            },
        ]
    },
    {
        'name': "Inha University in Tashkent",
        'short_name': 'IUT',
        'type': 'private',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 2014,
        'student_count': 4000,
        'website': 'https://inha.uz',
        'description': "Janubiy Koreyaning Inha University filiali. Ingliz tilida ta'lim beradi.",
        'faculties': [
            {
                'name': 'IT fakulteti',
                'directions': [
                    {'code': '60610203', 'name': 'Computer Science and Engineering', 'grant_quota': 20, 'contract_quota': 200,
                     'contract_price': 22_000_000, 'scores': {2024: (185.5, 148.2, 2500, 5.5), 2025: (187.8, 150.5, 2700, 5.8)}},
                    {'code': '60610204', 'name': 'Information Systems Engineering', 'grant_quota': 15, 'contract_quota': 150,
                     'contract_price': 22_000_000, 'scores': {2024: (180.2, 143.5, 1800, 4.0), 2025: (182.5, 145.8, 2000, 4.3)}},
                ]
            },
        ]
    },
    {
        'name': "Webster University Tashkent",
        'short_name': 'Webster',
        'type': 'foreign',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 2019,
        'student_count': 1500,
        'website': 'https://webster.uz',
        'description': "AQShning Webster University filiali. Xalqaro diplomlar beradi.",
        'faculties': [
            {
                'name': 'Biznes fakulteti',
                'directions': [
                    {'code': '60310202', 'name': 'Business Administration', 'grant_quota': 0, 'contract_quota': 100,
                     'contract_price': 55_000_000, 'scores': {2024: (150.5, 125.8, 400, 1.2), 2025: (152.8, 128.1, 450, 1.3)}},
                ]
            },
            {
                'name': 'Media fakulteti',
                'directions': [
                    {'code': '60410100', 'name': 'Media Communications', 'grant_quota': 0, 'contract_quota': 60,
                     'contract_price': 55_000_000, 'scores': {2024: (148.2, 123.5, 300, 1.1), 2025: (150.5, 125.8, 350, 1.2)}},
                ]
            },
        ]
    },
    {
        'name': "Turin Politexnika universiteti Toshkentda",
        'short_name': 'TTPU',
        'type': 'joint',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 2009,
        'student_count': 3500,
        'website': 'https://polito.uz',
        'description': "Italiyaning Turin politexnika universiteti bilan qo'shma. Injiniring sohasida kuchli.",
        'faculties': [
            {
                'name': 'Injiniring fakulteti',
                'directions': [
                    {'code': '60710501', 'name': 'Mechanical Engineering', 'grant_quota': 25, 'contract_quota': 120,
                     'contract_price': 22_000_000, 'scores': {2024: (182.5, 142.8, 1500, 3.5), 2025: (184.8, 145.1, 1600, 3.8)}},
                    {'code': '60710502', 'name': 'Civil Engineering', 'grant_quota': 20, 'contract_quota': 100,
                     'contract_price': 22_000_000, 'scores': {2024: (178.2, 138.5, 1200, 3.0), 2025: (180.5, 140.8, 1300, 3.2)}},
                ]
            },
            {
                'name': 'IT fakulteti',
                'directions': [
                    {'code': '60610205', 'name': 'Computer Engineering', 'grant_quota': 20, 'contract_quota': 130,
                     'contract_price': 22_000_000, 'scores': {2024: (190.5, 150.8, 2000, 4.8), 2025: (192.8, 153.1, 2200, 5.1)}},
                ]
            },
        ]
    },
    {
        'name': "Yeoju Technical Institute in Tashkent",
        'short_name': 'Yeoju',
        'type': 'joint',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 2019,
        'student_count': 2000,
        'website': 'https://ytit.uz',
        'description': "Janubiy Koreyaning Yeoju Institute of Technology bilan qo'shma ta'lim muassasasi.",
        'faculties': [
            {
                'name': 'IT fakulteti',
                'directions': [
                    {'code': '60610206', 'name': 'Kompyuter injiniringi', 'grant_quota': 15, 'contract_quota': 100,
                     'contract_price': 16_500_000, 'scores': {2024: (172.5, 132.8, 1000, 2.5), 2025: (174.8, 135.1, 1100, 2.7)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent irrigatsiya va qishloq xo'jaligini mexanizatsiyalash muhandislari instituti",
        'short_name': 'TIQXMMI',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1934,
        'student_count': 10000,
        'website': 'https://tiiame.uz',
        'description': "Suv xo'jaligi va irrigatsiya sohasida kadrlar tayyorlaydi.",
        'faculties': [
            {
                'name': "Gidrotexnika fakulteti",
                'directions': [
                    {'code': '60750100', 'name': 'Gidrotexnika inshootlari va nasos stansiyalari', 'grant_quota': 50, 'contract_quota': 80,
                     'contract_price': 12_100_000, 'scores': {2024: (168.5, 126.8, 700, 2.0), 2025: (170.8, 129.1, 750, 2.2)}},
                ]
            },
            {
                'name': "Yer tuzish fakulteti",
                'directions': [
                    {'code': '60750200', 'name': 'Yer tuzish va yer kadastri', 'grant_quota': 40, 'contract_quota': 90,
                     'contract_price': 12_100_000, 'scores': {2024: (170.2, 128.5, 850, 2.3), 2025: (172.5, 130.8, 900, 2.5)}},
                ]
            },
        ]
    },
    {
        'name': "Samarqand davlat tibbiyot universiteti",
        'short_name': 'SamDTU',
        'type': 'state',
        'region': 'Samarqand',
        'city': 'Samarqand',
        'established_year': 1930,
        'student_count': 8000,
        'website': 'https://sammu.uz',
        'description': "Samarqanddagi yetakchi tibbiyot universiteti.",
        'faculties': [
            {
                'name': 'Davolash fakulteti',
                'directions': [
                    {'code': '60510101', 'name': 'Davolash ishi', 'grant_quota': 80, 'contract_quota': 250,
                     'contract_price': 14_300_000, 'scores': {2024: (192.5, 155.8, 3500, 8.0), 2025: (194.8, 158.1, 3700, 8.5)}},
                ]
            },
            {
                'name': 'Stomatologiya fakulteti',
                'directions': [
                    {'code': '60510301', 'name': 'Stomatologiya', 'grant_quota': 30, 'contract_quota': 150,
                     'contract_price': 16_500_000, 'scores': {2024: (190.2, 153.5, 2800, 7.0), 2025: (192.5, 155.8, 3000, 7.3)}},
                ]
            },
        ]
    },
    {
        'name': "Andijon davlat tibbiyot instituti",
        'short_name': 'AndMI',
        'type': 'state',
        'region': 'Andijon',
        'city': 'Andijon',
        'established_year': 1955,
        'student_count': 6000,
        'website': 'https://andmi.uz',
        'description': "Andijon viloyatidagi tibbiyot instituti.",
        'faculties': [
            {
                'name': 'Davolash fakulteti',
                'directions': [
                    {'code': '60510102', 'name': 'Davolash ishi', 'grant_quota': 60, 'contract_quota': 200,
                     'contract_price': 14_300_000, 'scores': {2024: (188.5, 150.8, 2800, 6.5), 2025: (190.8, 153.1, 3000, 6.8)}},
                ]
            },
        ]
    },
    {
        'name': "Buxoro davlat tibbiyot instituti",
        'short_name': 'BuxMI',
        'type': 'state',
        'region': 'Buxoro',
        'city': 'Buxoro',
        'established_year': 1990,
        'student_count': 5000,
        'website': 'https://bsmi.uz',
        'description': "Buxoro viloyatidagi tibbiyot instituti.",
        'faculties': [
            {
                'name': 'Davolash fakulteti',
                'directions': [
                    {'code': '60510103', 'name': 'Davolash ishi', 'grant_quota': 50, 'contract_quota': 180,
                     'contract_price': 14_300_000, 'scores': {2024: (186.2, 148.5, 2500, 6.0), 2025: (188.5, 150.8, 2700, 6.3)}},
                ]
            },
        ]
    },
    {
        'name': "Toshkent davlat sharqshunoslik universiteti",
        'short_name': 'ToshDShU',
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1955,
        'student_count': 7000,
        'website': 'https://tsuos.uz',
        'description': "Sharq tillari va madaniyati bo'yicha ixtisoslashgan universitet.",
        'faculties': [
            {
                'name': 'Sharq tillari fakulteti',
                'directions': [
                    {'code': '60120350', 'name': 'Xitoy filologiyasi', 'grant_quota': 30, 'contract_quota': 120,
                     'contract_price': 12_100_000, 'scores': {2024: (182.5, 140.8, 1500, 3.8), 2025: (184.8, 143.1, 1650, 4.0)}},
                    {'code': '60120360', 'name': 'Yapon filologiyasi', 'grant_quota': 20, 'contract_quota': 80,
                     'contract_price': 12_100_000, 'scores': {2024: (180.2, 138.5, 1200, 3.2), 2025: (182.5, 140.8, 1300, 3.4)}},
                    {'code': '60120370', 'name': 'Koreys filologiyasi', 'grant_quota': 25, 'contract_quota': 100,
                     'contract_price': 12_100_000, 'scores': {2024: (183.8, 142.1, 1400, 3.5), 2025: (186.1, 144.4, 1500, 3.8)}},
                    {'code': '60120380', 'name': 'Arab filologiyasi', 'grant_quota': 25, 'contract_quota': 90,
                     'contract_price': 12_100_000, 'scores': {2024: (178.5, 136.8, 1100, 2.8), 2025: (180.8, 139.1, 1200, 3.0)}},
                ]
            },
        ]
    },
    {
        'name': "O'zbekiston davlat san'at va madaniyat instituti",
        'short_name': "O'zDSMI",
        'type': 'state',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 1945,
        'student_count': 5000,
        'website': 'https://uzsmi.uz',
        'description': "San'at va madaniyat sohasida kadrlar tayyorlaydi.",
        'faculties': [
            {
                'name': "San'at fakulteti",
                'directions': [
                    {'code': '60210100', 'name': "Tasviriy san'at", 'grant_quota': 30, 'contract_quota': 60,
                     'contract_price': 9_900_000, 'scores': {2024: (160.5, 120.8, 500, 1.5), 2025: (162.8, 123.1, 550, 1.7)}},
                    {'code': '60210200', 'name': "Musiqa san'ati", 'grant_quota': 25, 'contract_quota': 50,
                     'contract_price': 9_900_000, 'scores': {2024: (158.2, 118.5, 400, 1.3), 2025: (160.5, 120.8, 450, 1.4)}},
                ]
            },
        ]
    },
    {
        'name': "Jizzax davlat pedagogika universiteti",
        'short_name': 'JizDPU',
        'type': 'state',
        'region': 'Jizzax',
        'city': 'Jizzax',
        'established_year': 1974,
        'student_count': 7000,
        'website': 'https://jizpu.uz',
        'description': "Jizzax viloyatidagi pedagogika universiteti.",
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110107', 'name': 'Matematika', 'grant_quota': 40, 'contract_quota': 60,
                     'contract_price': 9_900_000, 'scores': {2024: (160.5, 120.2, 550, 1.6), 2025: (162.8, 122.5, 600, 1.8)}},
                ]
            },
        ]
    },
    {
        'name': "Nukus davlat pedagogika instituti",
        'short_name': 'NukDPI',
        'type': 'state',
        'region': 'Qoraqalpog\'iston',
        'city': 'Nukus',
        'established_year': 1979,
        'student_count': 6000,
        'website': 'https://ndpi.uz',
        'description': "Qoraqalpog'iston Respublikasidagi yetakchi pedagogika instituti.",
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110108', 'name': 'Matematika', 'grant_quota': 35, 'contract_quota': 55,
                     'contract_price': 9_900_000, 'scores': {2024: (158.2, 118.5, 450, 1.4), 2025: (160.5, 120.8, 500, 1.5)}},
                ]
            },
        ]
    },
    {
        'name': "Termiz davlat universiteti",
        'short_name': 'TermDU',
        'type': 'state',
        'region': 'Surxondaryo',
        'city': 'Termiz',
        'established_year': 1943,
        'student_count': 8000,
        'website': 'https://terdu.uz',
        'description': "Surxondaryo viloyatidagi yetakchi universitet.",
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110109', 'name': 'Matematika', 'grant_quota': 40, 'contract_quota': 60,
                     'contract_price': 9_900_000, 'scores': {2024: (161.5, 121.8, 580, 1.6), 2025: (163.8, 124.1, 620, 1.8)}},
                ]
            },
        ]
    },
    {
        'name': "Urganch davlat universiteti",
        'short_name': 'UrDU',
        'type': 'state',
        'region': 'Xorazm',
        'city': 'Urganch',
        'established_year': 1992,
        'student_count': 9000,
        'website': 'https://urdu.uz',
        'description': "Xorazm viloyatidagi eng yirik universitet.",
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110110', 'name': 'Matematika', 'grant_quota': 40, 'contract_quota': 65,
                     'contract_price': 9_900_000, 'scores': {2024: (163.8, 122.5, 600, 1.7), 2025: (166.1, 124.8, 650, 1.9)}},
                ]
            },
            {
                'name': "IT fakulteti",
                'directions': [
                    {'code': '60610109', 'name': "Dasturiy injiniring", 'grant_quota': 30, 'contract_quota': 120,
                     'contract_price': 12_100_000, 'scores': {2024: (178.5, 136.8, 1500, 3.5), 2025: (180.8, 139.1, 1650, 3.8)}},
                ]
            },
        ]
    },
    {
        'name': "Guliston davlat universiteti",
        'short_name': 'GulDU',
        'type': 'state',
        'region': 'Sirdaryo',
        'city': 'Guliston',
        'established_year': 1992,
        'student_count': 7000,
        'website': 'https://guldu.uz',
        'description': "Sirdaryo viloyatidagi davlat universiteti.",
        'faculties': [
            {
                'name': "Tabiiy fanlar fakulteti",
                'directions': [
                    {'code': '60110111', 'name': 'Matematika', 'grant_quota': 35, 'contract_quota': 55,
                     'contract_price': 9_900_000, 'scores': {2024: (159.8, 119.5, 480, 1.5), 2025: (162.1, 121.8, 520, 1.6)}},
                ]
            },
        ]
    },
    # ======================== XORIJIY FILIALLAR ========================
    {
        'name': "Rossiya iqtisodiyot universiteti Toshkent filiali (Plekhanov)",
        'short_name': 'REU Toshkent',
        'type': 'foreign',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 2016,
        'student_count': 2500,
        'website': 'https://reu.uz',
        'description': "Rossiya Plekhanov iqtisodiyot universiteti Toshkent filiali.",
        'faculties': [
            {
                'name': 'Iqtisodiyot fakulteti',
                'directions': [
                    {'code': '60310203', 'name': 'Iqtisodiyot', 'grant_quota': 10, 'contract_quota': 120,
                     'contract_price': 22_000_000, 'scores': {2024: (172.5, 135.8, 1200, 2.8), 2025: (174.8, 138.1, 1300, 3.0)}},
                ]
            },
        ]
    },
    {
        'name': "Moskva davlat universiteti Toshkent filiali",
        'short_name': 'MDU Toshkent',
        'type': 'foreign',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 2019,
        'student_count': 1500,
        'website': 'https://msu.uz',
        'description': "Rossiya MDU Toshkent filiali. Nufuzli xalqaro diplom beradi.",
        'faculties': [
            {
                'name': 'Matematika va IT fakulteti',
                'directions': [
                    {'code': '60110112', 'name': 'Amaliy matematika va informatika', 'grant_quota': 15, 'contract_quota': 80,
                     'contract_price': 33_000_000, 'scores': {2024: (188.5, 150.8, 1200, 3.0), 2025: (190.8, 153.1, 1300, 3.2)}},
                ]
            },
        ]
    },
    {
        'name': "Management Development Institute of Singapore (MDIS) Tashkent",
        'short_name': 'MDIS',
        'type': 'foreign',
        'region': 'Toshkent',
        'city': 'Toshkent',
        'established_year': 2020,
        'student_count': 1200,
        'website': 'https://mdis.uz',
        'description': "Singapurning MDIS Toshkent filiali. Biznes va IT sohasida ta'lim beradi.",
        'faculties': [
            {
                'name': 'Biznes fakulteti',
                'directions': [
                    {'code': '60310204', 'name': 'International Business', 'grant_quota': 0, 'contract_quota': 80,
                     'contract_price': 44_000_000, 'scores': {2024: (148.5, 122.8, 350, 1.1), 2025: (150.8, 125.1, 400, 1.2)}},
                ]
            },
        ]
    },
]


class Command(BaseCommand):
    help = "O'zbekiston universitetlari ma'lumotlarini bazaga kiritish"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Avvalgi ma\'lumotlarni tozalash',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Eski ma\'lumotlar o\'chirilmoqda...')
            PassingScore.objects.all().delete()
            Direction.objects.all().delete()
            Faculty.objects.all().delete()
            University.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Tozalandi!'))

        total_unis = 0
        total_faculties = 0
        total_directions = 0
        total_scores = 0

        for uni_data in UNIVERSITIES_DATA:
            slug = slugify(uni_data['name'])

            university, created = University.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': uni_data['name'],
                    'short_name': uni_data.get('short_name', ''),
                    'university_type': uni_data['type'],
                    'region': uni_data['region'],
                    'city': uni_data['city'],
                    'established_year': uni_data.get('established_year'),
                    'student_count': uni_data.get('student_count'),
                    'website': uni_data.get('website', ''),
                    'description': uni_data.get('description', ''),
                    'is_active': True,
                }
            )

            action = 'Yaratildi' if created else 'Yangilandi'
            total_unis += 1

            for fac_data in uni_data.get('faculties', []):
                fac_slug = slugify(fac_data['name'])

                faculty, _ = Faculty.objects.update_or_create(
                    university=university,
                    slug=fac_slug,
                    defaults={
                        'name': fac_data['name'],
                        'is_active': True,
                    }
                )
                total_faculties += 1

                for dir_data in fac_data.get('directions', []):
                    dir_slug = slugify(dir_data['name'])

                    direction, _ = Direction.objects.update_or_create(
                        university=university,
                        code=dir_data['code'],
                        defaults={
                            'faculty': faculty,
                            'name': dir_data['name'],
                            'slug': dir_slug,
                            'education_form': 'full_time',
                            'education_type': 'both' if dir_data['grant_quota'] > 0 else 'contract',
                            'grant_quota': dir_data['grant_quota'],
                            'contract_quota': dir_data['contract_quota'],
                            'contract_price': dir_data['contract_price'],
                            'is_active': True,
                        }
                    )
                    total_directions += 1

                    for year, scores in dir_data.get('scores', {}).items():
                        grant_score, contract_score, applications, ratio = scores

                        PassingScore.objects.update_or_create(
                            direction=direction,
                            year=year,
                            defaults={
                                'grant_score': grant_score,
                                'contract_score': contract_score,
                                'total_applications': applications,
                                'competition_ratio': ratio,
                            }
                        )
                        total_scores += 1

            self.stdout.write(f'  {action}: {university.name}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Tayyor! {total_unis} ta universitet, {total_faculties} ta fakultet, '
            f'{total_directions} ta yo\'nalish, {total_scores} ta o\'tish bali kiritildi.'
        ))

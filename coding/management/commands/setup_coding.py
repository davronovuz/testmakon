"""
TestMakon.uz — Dasturlash tillari, kategoriyalar va masalalarni yaratish
Usage: python manage.py setup_coding
"""

from django.core.management.base import BaseCommand
from coding.models import ProgrammingLanguage, CodingCategory, CodingProblem, TestCase


class Command(BaseCommand):
    help = "Dasturlash tillari, kategoriyalar va masalalarni yaratish"

    def handle(self, *args, **options):
        self._create_languages()
        self._cleanup_old_categories()
        self._create_categories()
        self._create_problems()

    def _cleanup_old_categories(self):
        """Eski kategoriyalarni o'chirish (masala bog'lanmagan)"""
        old_slugs = ['array', 'recursion', 'dp']
        deleted = CodingCategory.objects.filter(slug__in=old_slugs, problems__isnull=True).delete()[0]
        if deleted:
            self.stdout.write(f"  {deleted} ta eski kategoriya o'chirildi")

    def _create_languages(self):
        languages = [
            {
                'name': 'Python',
                'slug': 'python',
                'docker_image': 'python:3.12-slim',
                'compile_cmd': '',
                'run_cmd': 'python3 {file}',
                'file_extension': '.py',
                'monaco_language': 'python',
                'order': 1,
            },
            {
                'name': 'C++',
                'slug': 'cpp',
                'docker_image': 'gcc:13-bookworm',
                'compile_cmd': 'g++ -O2 -o /tmp/solution {file}',
                'run_cmd': '/tmp/solution',
                'file_extension': '.cpp',
                'monaco_language': 'cpp',
                'order': 2,
            },
            {
                'name': 'Java',
                'slug': 'java',
                'docker_image': 'openjdk:21-slim',
                'compile_cmd': 'javac -d /tmp {file}',
                'run_cmd': 'java -cp /tmp Solution',
                'file_extension': '.java',
                'monaco_language': 'java',
                'order': 3,
            },
            {
                'name': 'JavaScript',
                'slug': 'javascript',
                'docker_image': 'node:20-slim',
                'compile_cmd': '',
                'run_cmd': 'node {file}',
                'file_extension': '.js',
                'monaco_language': 'javascript',
                'order': 4,
            },
        ]
        for data in languages:
            obj, created = ProgrammingLanguage.objects.update_or_create(slug=data['slug'], defaults=data)
            self.stdout.write(f"  {'✓' if created else '~'} {obj.name}")
        self.stdout.write(self.style.SUCCESS(f"  {len(languages)} til tayyor\n"))

    def _create_categories(self):
        categories = [
            {'name': 'int — Sonlar', 'slug': 'int', 'icon': 'bi-123', 'order': 1},
            {'name': 'str — Satrlar', 'slug': 'str', 'icon': 'bi-fonts', 'order': 2},
            {'name': 'list — Ro\'yxatlar', 'slug': 'list', 'icon': 'bi-list-ol', 'order': 3},
            {'name': 'tuple — Kortejlar', 'slug': 'tuple', 'icon': 'bi-collection', 'order': 4},
            {'name': 'dict — Lug\'atlar', 'slug': 'dict', 'icon': 'bi-book', 'order': 5},
            {'name': 'def — Funksiyalar', 'slug': 'def', 'icon': 'bi-braces', 'order': 6},
            {'name': 'Sorting — Tartiblash', 'slug': 'sorting', 'icon': 'bi-sort-down', 'order': 7},
            {'name': 'Math — Matematika', 'slug': 'math', 'icon': 'bi-calculator', 'order': 8},
        ]
        for data in categories:
            obj, created = CodingCategory.objects.update_or_create(slug=data['slug'], defaults=data)
            self.stdout.write(f"  {'✓' if created else '~'} {obj.name}")
        self.stdout.write(self.style.SUCCESS(f"  {len(categories)} kategoriya tayyor\n"))

    def _create_problems(self):
        python = ProgrammingLanguage.objects.get(slug='python')
        all_langs = list(ProgrammingLanguage.objects.filter(is_active=True))

        problems_data = [
            # ═══════════════════════════════════════════
            # int — Sonlar (1-5)
            # ═══════════════════════════════════════════
            {
                'title': 'Ikki sonni qo\'shish',
                'slug': 'ikki-sonni-qoshish',
                'description': 'Ikki butun son berilgan. Ularning yig\'indisini toping.',
                'input_format': 'Bitta qatorda bo\'sh joy bilan ajratilgan ikki butun son <code>a</code> va <code>b</code> beriladi.',
                'output_format': '<code>a + b</code> yig\'indisini chiqaring.',
                'constraints': '-10<sup>9</sup> ≤ a, b ≤ 10<sup>9</sup>',
                'difficulty': 'easy',
                'category_slug': 'int',
                'order': 1,
                'time_limit': 1,
                'starter_code': {
                    'python': 'a, b = map(int, input().split())\nprint(a + b)',
                    'cpp': '#include <iostream>\nusing namespace std;\nint main() {\n    long long a, b;\n    cin >> a >> b;\n    cout << a + b << endl;\n    return 0;\n}',
                    'java': 'import java.util.Scanner;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        long a = sc.nextLong(), b = sc.nextLong();\n        System.out.println(a + b);\n    }\n}',
                    'javascript': 'const [a, b] = require("fs").readFileSync("/dev/stdin", "utf8").trim().split(" ").map(Number);\nconsole.log(a + b);',
                },
                'languages': 'all',
                'test_cases': [
                    {'input': '3 5', 'output': '8', 'is_sample': True, 'order': 1},
                    {'input': '10 20', 'output': '30', 'is_sample': True, 'order': 2},
                    {'input': '-5 5', 'output': '0', 'is_sample': False, 'order': 3},
                    {'input': '0 0', 'output': '0', 'is_sample': False, 'order': 4},
                    {'input': '1000000000 1000000000', 'output': '2000000000', 'is_sample': False, 'order': 5},
                    {'input': '-1000000000 -1000000000', 'output': '-2000000000', 'is_sample': False, 'order': 6},
                ],
            },
            {
                'title': 'Juft yoki toq',
                'slug': 'juft-yoki-toq',
                'description': 'Butun son berilgan. U juft yoki toq ekanligini aniqlang.',
                'input_format': 'Bitta butun son <code>n</code> beriladi.',
                'output_format': 'Agar son juft bo\'lsa <code>Juft</code>, aks holda <code>Toq</code> deb chiqaring.',
                'constraints': '-10<sup>9</sup> ≤ n ≤ 10<sup>9</sup>',
                'difficulty': 'easy',
                'category_slug': 'int',
                'order': 2,
                'time_limit': 1,
                'starter_code': {'python': 'n = int(input())\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '4', 'output': 'Juft', 'is_sample': True, 'order': 1},
                    {'input': '7', 'output': 'Toq', 'is_sample': True, 'order': 2},
                    {'input': '0', 'output': 'Juft', 'is_sample': False, 'order': 3},
                    {'input': '-3', 'output': 'Toq', 'is_sample': False, 'order': 4},
                    {'input': '-8', 'output': 'Juft', 'is_sample': False, 'order': 5},
                    {'input': '1', 'output': 'Toq', 'is_sample': False, 'order': 6},
                ],
            },
            {
                'title': 'Uch sondan eng kattasi',
                'slug': 'uch-sondan-eng-kattasi',
                'description': 'Uchta butun son berilgan. Ulardan eng kattasini toping.',
                'input_format': 'Bitta qatorda uchta butun son <code>a</code>, <code>b</code>, <code>c</code> beriladi.',
                'output_format': 'Eng katta sonni chiqaring.',
                'constraints': '-10<sup>9</sup> ≤ a, b, c ≤ 10<sup>9</sup>',
                'difficulty': 'easy',
                'category_slug': 'int',
                'order': 3,
                'time_limit': 1,
                'starter_code': {'python': 'a, b, c = map(int, input().split())\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '1 2 3', 'output': '3', 'is_sample': True, 'order': 1},
                    {'input': '10 5 8', 'output': '10', 'is_sample': True, 'order': 2},
                    {'input': '-1 -2 -3', 'output': '-1', 'is_sample': False, 'order': 3},
                    {'input': '5 5 5', 'output': '5', 'is_sample': False, 'order': 4},
                    {'input': '0 -1 1', 'output': '1', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Raqamlar yig\'indisi',
                'slug': 'raqamlar-yigindisi',
                'description': 'Musbat butun son berilgan. Uning raqamlari yig\'indisini toping.',
                'input_format': 'Bitta musbat butun son <code>n</code> beriladi.',
                'output_format': 'Sonning raqamlari yig\'indisini chiqaring.',
                'constraints': '1 ≤ n ≤ 10<sup>18</sup>',
                'difficulty': 'easy',
                'category_slug': 'int',
                'order': 4,
                'time_limit': 1,
                'starter_code': {'python': 'n = input()\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '123', 'output': '6', 'is_sample': True, 'order': 1},
                    {'input': '9999', 'output': '36', 'is_sample': True, 'order': 2},
                    {'input': '1', 'output': '1', 'is_sample': False, 'order': 3},
                    {'input': '10', 'output': '1', 'is_sample': False, 'order': 4},
                    {'input': '999999999999999999', 'output': '162', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Bo\'luvchilar soni',
                'slug': 'boluvchilar-soni',
                'description': 'Musbat butun son berilgan. Uning bo\'luvchilar sonini toping.',
                'input_format': 'Bitta musbat butun son <code>n</code> beriladi.',
                'output_format': '<code>n</code> ning bo\'luvchilar sonini chiqaring.',
                'constraints': '1 ≤ n ≤ 10<sup>6</sup>',
                'difficulty': 'medium',
                'category_slug': 'int',
                'order': 5,
                'time_limit': 2,
                'starter_code': {'python': 'n = int(input())\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '6', 'output': '4', 'is_sample': True, 'order': 1},
                    {'input': '12', 'output': '6', 'is_sample': True, 'order': 2},
                    {'input': '1', 'output': '1', 'is_sample': False, 'order': 3},
                    {'input': '7', 'output': '2', 'is_sample': False, 'order': 4},
                    {'input': '100', 'output': '9', 'is_sample': False, 'order': 5},
                    {'input': '1000000', 'output': '49', 'is_sample': False, 'order': 6},
                ],
            },

            # ═══════════════════════════════════════════
            # str — Satrlar (6-10)
            # ═══════════════════════════════════════════
            {
                'title': 'Satrni teskari qilish',
                'slug': 'satrni-teskari-qilish',
                'description': 'Satr berilgan. Uni teskari tartibda chiqaring.',
                'input_format': 'Bitta satr <code>s</code> beriladi.',
                'output_format': 'Teskari satrni chiqaring.',
                'constraints': '1 ≤ |s| ≤ 10<sup>5</sup>',
                'difficulty': 'easy',
                'category_slug': 'str',
                'order': 6,
                'time_limit': 1,
                'starter_code': {'python': 's = input()\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': 'salom', 'output': 'molas', 'is_sample': True, 'order': 1},
                    {'input': 'abcd', 'output': 'dcba', 'is_sample': True, 'order': 2},
                    {'input': 'a', 'output': 'a', 'is_sample': False, 'order': 3},
                    {'input': 'ab', 'output': 'ba', 'is_sample': False, 'order': 4},
                    {'input': '12345', 'output': '54321', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Palindrom tekshirish',
                'slug': 'palindrom-tekshirish',
                'description': 'Satr berilgan. U palindrom (chapdan va o\'ngdan bir xil o\'qiladi) yoki yo\'qligini aniqlang.',
                'input_format': 'Bitta satr <code>s</code> beriladi (faqat kichik lotin harflari).',
                'output_format': 'Palindrom bo\'lsa <code>HA</code>, aks holda <code>YOQ</code> deb chiqaring.',
                'constraints': '1 ≤ |s| ≤ 10<sup>5</sup>',
                'difficulty': 'easy',
                'category_slug': 'str',
                'order': 7,
                'time_limit': 1,
                'starter_code': {'python': 's = input()\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': 'aba', 'output': 'HA', 'is_sample': True, 'order': 1},
                    {'input': 'salom', 'output': 'YOQ', 'is_sample': True, 'order': 2},
                    {'input': 'a', 'output': 'HA', 'is_sample': False, 'order': 3},
                    {'input': 'abba', 'output': 'HA', 'is_sample': False, 'order': 4},
                    {'input': 'abca', 'output': 'YOQ', 'is_sample': False, 'order': 5},
                    {'input': 'racecar', 'output': 'HA', 'is_sample': False, 'order': 6},
                ],
            },
            {
                'title': 'So\'zlar sonini hisoblash',
                'slug': 'sozlar-sonini-hisoblash',
                'description': 'Satr berilgan. Undagi so\'zlar sonini toping. So\'zlar bo\'sh joy bilan ajratilgan.',
                'input_format': 'Bitta satr beriladi.',
                'output_format': 'So\'zlar sonini chiqaring.',
                'constraints': '1 ≤ |s| ≤ 10<sup>5</sup>. Satr boshida va oxirida bo\'sh joy bo\'lishi mumkin.',
                'difficulty': 'easy',
                'category_slug': 'str',
                'order': 8,
                'time_limit': 1,
                'starter_code': {'python': 's = input()\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': 'salom dunyo', 'output': '2', 'is_sample': True, 'order': 1},
                    {'input': 'bir ikki uch tort', 'output': '4', 'is_sample': True, 'order': 2},
                    {'input': 'salom', 'output': '1', 'is_sample': False, 'order': 3},
                    {'input': '  salom  dunyo  ', 'output': '2', 'is_sample': False, 'order': 4},
                    {'input': 'a b c d e', 'output': '5', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Katta harfga aylantirish',
                'slug': 'katta-harfga-aylantirish',
                'description': 'Satr berilgan. Har bir so\'zning birinchi harfini katta harf qiling.',
                'input_format': 'Bitta satr beriladi.',
                'output_format': 'Har bir so\'z bosh harfi katta qilingan satrni chiqaring.',
                'constraints': '1 ≤ |s| ≤ 10<sup>5</sup>',
                'difficulty': 'easy',
                'category_slug': 'str',
                'order': 9,
                'time_limit': 1,
                'starter_code': {'python': 's = input()\n'},
                'languages': 'python',
                'test_cases': [
                    {'input': 'salom dunyo', 'output': 'Salom Dunyo', 'is_sample': True, 'order': 1},
                    {'input': 'python dasturlash tili', 'output': 'Python Dasturlash Tili', 'is_sample': True, 'order': 2},
                    {'input': 'a', 'output': 'A', 'is_sample': False, 'order': 3},
                    {'input': 'bir', 'output': 'Bir', 'is_sample': False, 'order': 4},
                    {'input': 'KATTA harf', 'output': 'Katta Harf', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Eng ko\'p takrorlangan harf',
                'slug': 'eng-kop-takrorlangan-harf',
                'description': 'Satr berilgan. Eng ko\'p takrorlangan harfni va uning sonini toping. Bir nechta harf teng bo\'lsa, alifbo bo\'yicha birinchisini chiqaring.',
                'input_format': 'Bitta satr <code>s</code> beriladi (faqat kichik lotin harflari).',
                'output_format': 'Eng ko\'p takrorlangan harf va uning sonini bo\'sh joy bilan ajratib chiqaring.',
                'constraints': '1 ≤ |s| ≤ 10<sup>5</sup>',
                'difficulty': 'medium',
                'category_slug': 'str',
                'order': 10,
                'time_limit': 1,
                'starter_code': {'python': 's = input()\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': 'aabbbcc', 'output': 'b 3', 'is_sample': True, 'order': 1},
                    {'input': 'abcabc', 'output': 'a 2', 'is_sample': True, 'order': 2},
                    {'input': 'z', 'output': 'z 1', 'is_sample': False, 'order': 3},
                    {'input': 'aabb', 'output': 'a 2', 'is_sample': False, 'order': 4},
                    {'input': 'zzzzz', 'output': 'z 5', 'is_sample': False, 'order': 5},
                ],
            },

            # ═══════════════════════════════════════════
            # list — Ro'yxatlar (11-15)
            # ═══════════════════════════════════════════
            {
                'title': 'Ro\'yxat yig\'indisi',
                'slug': 'royxat-yigindisi',
                'description': 'Butun sonlar ro\'yxati berilgan. Ularning yig\'indisini toping.',
                'input_format': 'Birinchi qatorda <code>n</code> — elementlar soni. Ikkinchi qatorda <code>n</code> ta butun son.',
                'output_format': 'Ro\'yxat elementlari yig\'indisini chiqaring.',
                'constraints': '1 ≤ n ≤ 10<sup>5</sup>, -10<sup>9</sup> ≤ a<sub>i</sub> ≤ 10<sup>9</sup>',
                'difficulty': 'easy',
                'category_slug': 'list',
                'order': 11,
                'time_limit': 1,
                'starter_code': {'python': 'n = int(input())\nnums = list(map(int, input().split()))\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '5\n1 2 3 4 5', 'output': '15', 'is_sample': True, 'order': 1},
                    {'input': '3\n10 -5 3', 'output': '8', 'is_sample': True, 'order': 2},
                    {'input': '1\n0', 'output': '0', 'is_sample': False, 'order': 3},
                    {'input': '4\n-1 -2 -3 -4', 'output': '-10', 'is_sample': False, 'order': 4},
                    {'input': '3\n1000000000 1000000000 1000000000', 'output': '3000000000', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Eng katta va eng kichik',
                'slug': 'eng-katta-va-eng-kichik',
                'description': 'Butun sonlar ro\'yxati berilgan. Eng katta va eng kichik elementni toping.',
                'input_format': 'Birinchi qatorda <code>n</code>. Ikkinchi qatorda <code>n</code> ta son.',
                'output_format': 'Bitta qatorda eng katta va eng kichik sonni bo\'sh joy bilan chiqaring.',
                'constraints': '1 ≤ n ≤ 10<sup>5</sup>',
                'difficulty': 'easy',
                'category_slug': 'list',
                'order': 12,
                'time_limit': 1,
                'starter_code': {'python': 'n = int(input())\nnums = list(map(int, input().split()))\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '5\n3 1 4 1 5', 'output': '5 1', 'is_sample': True, 'order': 1},
                    {'input': '3\n-5 0 5', 'output': '5 -5', 'is_sample': True, 'order': 2},
                    {'input': '1\n42', 'output': '42 42', 'is_sample': False, 'order': 3},
                    {'input': '4\n1 1 1 1', 'output': '1 1', 'is_sample': False, 'order': 4},
                    {'input': '3\n-100 -200 -50', 'output': '-50 -200', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Juft sonlarni ajratish',
                'slug': 'juft-sonlarni-ajratish',
                'description': 'Butun sonlar ro\'yxati berilgan. Faqat juft sonlarni tartibi bilan chiqaring.',
                'input_format': 'Birinchi qatorda <code>n</code>. Ikkinchi qatorda <code>n</code> ta son.',
                'output_format': 'Juft sonlarni bo\'sh joy bilan ajratib chiqaring. Juft son bo\'lmasa <code>-1</code> chiqaring.',
                'constraints': '1 ≤ n ≤ 10<sup>5</sup>',
                'difficulty': 'easy',
                'category_slug': 'list',
                'order': 13,
                'time_limit': 1,
                'starter_code': {'python': 'n = int(input())\nnums = list(map(int, input().split()))\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '5\n1 2 3 4 5', 'output': '2 4', 'is_sample': True, 'order': 1},
                    {'input': '4\n2 4 6 8', 'output': '2 4 6 8', 'is_sample': True, 'order': 2},
                    {'input': '3\n1 3 5', 'output': '-1', 'is_sample': False, 'order': 3},
                    {'input': '1\n0', 'output': '0', 'is_sample': False, 'order': 4},
                    {'input': '4\n-2 3 -4 5', 'output': '-2 -4', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Ro\'yxatni teskari qilish',
                'slug': 'royxatni-teskari-qilish',
                'description': 'Butun sonlar ro\'yxati berilgan. Uni teskari tartibda chiqaring.',
                'input_format': 'Birinchi qatorda <code>n</code>. Ikkinchi qatorda <code>n</code> ta son.',
                'output_format': 'Teskari tartibda, bo\'sh joy bilan ajratib chiqaring.',
                'constraints': '1 ≤ n ≤ 10<sup>5</sup>',
                'difficulty': 'easy',
                'category_slug': 'list',
                'order': 14,
                'time_limit': 1,
                'starter_code': {'python': 'n = int(input())\nnums = list(map(int, input().split()))\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '5\n1 2 3 4 5', 'output': '5 4 3 2 1', 'is_sample': True, 'order': 1},
                    {'input': '3\n10 20 30', 'output': '30 20 10', 'is_sample': True, 'order': 2},
                    {'input': '1\n5', 'output': '5', 'is_sample': False, 'order': 3},
                    {'input': '2\n-1 1', 'output': '1 -1', 'is_sample': False, 'order': 4},
                ],
            },
            {
                'title': 'Takrorlanmaydigan elementlar',
                'slug': 'takrorlanmaydigan-elementlar',
                'description': 'Butun sonlar ro\'yxati berilgan. Faqat bir marta uchraydigan elementlarni topib, tartib bo\'yicha chiqaring.',
                'input_format': 'Birinchi qatorda <code>n</code>. Ikkinchi qatorda <code>n</code> ta son.',
                'output_format': 'Faqat bir marta uchraydigan sonlarni bo\'sh joy bilan chiqaring. Bo\'lmasa <code>-1</code> chiqaring.',
                'constraints': '1 ≤ n ≤ 10<sup>5</sup>',
                'difficulty': 'medium',
                'category_slug': 'list',
                'order': 15,
                'time_limit': 1,
                'starter_code': {'python': 'n = int(input())\nnums = list(map(int, input().split()))\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '5\n1 2 2 3 3', 'output': '1', 'is_sample': True, 'order': 1},
                    {'input': '6\n4 5 6 4 5 7', 'output': '6 7', 'is_sample': True, 'order': 2},
                    {'input': '3\n1 1 1', 'output': '-1', 'is_sample': False, 'order': 3},
                    {'input': '4\n1 2 3 4', 'output': '1 2 3 4', 'is_sample': False, 'order': 4},
                    {'input': '1\n5', 'output': '5', 'is_sample': False, 'order': 5},
                ],
            },

            # ═══════════════════════════════════════════
            # tuple — Kortejlar (16-18)
            # ═══════════════════════════════════════════
            {
                'title': 'Koordinata masofasi',
                'slug': 'koordinata-masofasi',
                'description': 'Ikki nuqta (x1, y1) va (x2, y2) koordinatalari berilgan. Ular orasidagi Evklid masofasini toping.',
                'input_format': 'Birinchi qatorda <code>x1 y1</code>, ikkinchi qatorda <code>x2 y2</code>.',
                'output_format': 'Masofani 2 kasr raqamga yaxlitlab chiqaring.',
                'constraints': '-1000 ≤ x, y ≤ 1000',
                'difficulty': 'easy',
                'category_slug': 'tuple',
                'order': 16,
                'time_limit': 1,
                'starter_code': {'python': 'x1, y1 = map(int, input().split())\nx2, y2 = map(int, input().split())\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '0 0\n3 4', 'output': '5.00', 'is_sample': True, 'order': 1},
                    {'input': '1 1\n4 5', 'output': '5.00', 'is_sample': True, 'order': 2},
                    {'input': '0 0\n0 0', 'output': '0.00', 'is_sample': False, 'order': 3},
                    {'input': '-3 -4\n0 0', 'output': '5.00', 'is_sample': False, 'order': 4},
                    {'input': '1 0\n0 1', 'output': '1.41', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Talabalar reytingi',
                'slug': 'talabalar-reytingi',
                'description': 'N ta talabaning ismi va bali berilgan. Eng yuqori ball olgan talaba ismini chiqaring.',
                'input_format': 'Birinchi qatorda <code>n</code>. Keyingi <code>n</code> qatorda ism va bal (bo\'sh joy bilan).',
                'output_format': 'Eng yuqori ball olgan talaba ismini chiqaring.',
                'constraints': '1 ≤ n ≤ 1000, 0 ≤ bal ≤ 100',
                'difficulty': 'easy',
                'category_slug': 'tuple',
                'order': 17,
                'time_limit': 1,
                'starter_code': {'python': 'n = int(input())\n'},
                'languages': 'python',
                'test_cases': [
                    {'input': '3\nAli 85\nVali 92\nGani 78', 'output': 'Vali', 'is_sample': True, 'order': 1},
                    {'input': '2\nAnvar 50\nBobur 50', 'output': 'Anvar', 'is_sample': True, 'order': 2},
                    {'input': '1\nTest 100', 'output': 'Test', 'is_sample': False, 'order': 3},
                    {'input': '4\nA 10\nB 20\nC 30\nD 25', 'output': 'C', 'is_sample': False, 'order': 4},
                ],
            },
            {
                'title': 'Juftliklarni tartiblash',
                'slug': 'juftliklarni-tartiblash',
                'description': 'N ta (x, y) juftlik berilgan. Ularni birinchi elementga ko\'ra o\'sish tartibida, teng bo\'lsa ikkinchi elementga ko\'ra tartiblang.',
                'input_format': 'Birinchi qatorda <code>n</code>. Keyingi <code>n</code> qatorda ikki son.',
                'output_format': 'Tartiblangan juftliklarni har biri alohida qatorda chiqaring.',
                'constraints': '1 ≤ n ≤ 1000',
                'difficulty': 'medium',
                'category_slug': 'tuple',
                'order': 18,
                'time_limit': 1,
                'starter_code': {'python': 'n = int(input())\npairs = []\nfor _ in range(n):\n    x, y = map(int, input().split())\n    pairs.append((x, y))\n'},
                'languages': 'python',
                'test_cases': [
                    {'input': '3\n3 1\n1 2\n2 3', 'output': '1 2\n2 3\n3 1', 'is_sample': True, 'order': 1},
                    {'input': '3\n1 3\n1 1\n1 2', 'output': '1 1\n1 2\n1 3', 'is_sample': True, 'order': 2},
                    {'input': '1\n5 5', 'output': '5 5', 'is_sample': False, 'order': 3},
                    {'input': '4\n2 1\n1 2\n2 2\n1 1', 'output': '1 1\n1 2\n2 1\n2 2', 'is_sample': False, 'order': 4},
                ],
            },

            # ═══════════════════════════════════════════
            # dict — Lug'atlar (19-22)
            # ═══════════════════════════════════════════
            {
                'title': 'Harflar chastotasi',
                'slug': 'harflar-chastotasi',
                'description': 'Satr berilgan. Har bir harfning necha marta uchrashini alifbo tartibida chiqaring.',
                'input_format': 'Bitta satr (faqat kichik lotin harflari).',
                'output_format': 'Har bir harf va uning soni alohida qatorda, alifbo tartibida.',
                'constraints': '1 ≤ |s| ≤ 10<sup>5</sup>',
                'difficulty': 'easy',
                'category_slug': 'dict',
                'order': 19,
                'time_limit': 1,
                'starter_code': {'python': 's = input()\n'},
                'languages': 'python',
                'test_cases': [
                    {'input': 'abcab', 'output': 'a 2\nb 2\nc 1', 'is_sample': True, 'order': 1},
                    {'input': 'aaa', 'output': 'a 3', 'is_sample': True, 'order': 2},
                    {'input': 'z', 'output': 'z 1', 'is_sample': False, 'order': 3},
                    {'input': 'abcdef', 'output': 'a 1\nb 1\nc 1\nd 1\ne 1\nf 1', 'is_sample': False, 'order': 4},
                    {'input': 'banana', 'output': 'a 3\nb 1\nn 2', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'So\'z chastotasi',
                'slug': 'soz-chastotasi',
                'description': 'Matn berilgan. Har bir so\'zning necha marta uchrashini ko\'p uchragan so\'zdan boshlab chiqaring. Teng bo\'lsa alifbo tartibida.',
                'input_format': 'Bitta qatorda matn beriladi.',
                'output_format': 'Har bir so\'z va soni alohida qatorda.',
                'constraints': '1 ≤ so\'zlar soni ≤ 1000',
                'difficulty': 'medium',
                'category_slug': 'dict',
                'order': 20,
                'time_limit': 1,
                'starter_code': {'python': 'text = input()\n'},
                'languages': 'python',
                'test_cases': [
                    {'input': 'olma olma banan olma banan', 'output': 'olma 3\nbanan 2', 'is_sample': True, 'order': 1},
                    {'input': 'a b a b a', 'output': 'a 3\nb 2', 'is_sample': True, 'order': 2},
                    {'input': 'test', 'output': 'test 1', 'is_sample': False, 'order': 3},
                    {'input': 'c b a c b a', 'output': 'a 2\nb 2\nc 2', 'is_sample': False, 'order': 4},
                ],
            },
            {
                'title': 'Ikki ro\'yxat kesishmasi',
                'slug': 'ikki-royxat-kesishmasi',
                'description': 'Ikki ro\'yxat berilgan. Ikkala ro\'yxatda ham mavjud bo\'lgan elementlarni o\'sish tartibida chiqaring (takrorlanmasdan).',
                'input_format': 'Birinchi qatorda <code>n</code> va <code>n</code> ta son. Ikkinchi qatorda <code>m</code> va <code>m</code> ta son.',
                'output_format': 'Kesishma elementlarini o\'sish tartibida, bo\'sh joy bilan chiqaring. Bo\'lmasa <code>-1</code>.',
                'constraints': '1 ≤ n, m ≤ 10<sup>5</sup>',
                'difficulty': 'medium',
                'category_slug': 'dict',
                'order': 21,
                'time_limit': 1,
                'starter_code': {'python': 'n, *a = map(int, input().split())\nm, *b = map(int, input().split())\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '4 1 2 3 4\n3 3 4 5', 'output': '3 4', 'is_sample': True, 'order': 1},
                    {'input': '3 1 2 3\n3 4 5 6', 'output': '-1', 'is_sample': True, 'order': 2},
                    {'input': '5 1 1 2 2 3\n4 2 2 3 3', 'output': '2 3', 'is_sample': False, 'order': 3},
                    {'input': '1 5\n1 5', 'output': '5', 'is_sample': False, 'order': 4},
                ],
            },
            {
                'title': 'Telefon daftarchasi',
                'slug': 'telefon-daftarchasi',
                'description': 'N ta kontakt (ism va raqam) beriladi. Keyin Q ta so\'rov keladi — ism bo\'yicha raqam toping.',
                'input_format': 'Birinchi qatorda <code>n</code>. Keyingi <code>n</code> qatorda ism va raqam. Keyin <code>q</code>. Keyingi <code>q</code> qatorda qidirilayotgan ism.',
                'output_format': 'Har bir so\'rov uchun raqamni yoki <code>Topilmadi</code> deb chiqaring.',
                'constraints': '1 ≤ n, q ≤ 1000',
                'difficulty': 'easy',
                'category_slug': 'dict',
                'order': 22,
                'time_limit': 1,
                'starter_code': {'python': 'n = int(input())\ncontacts = {}\nfor _ in range(n):\n    name, number = input().split()\n    contacts[name] = number\n'},
                'languages': 'python',
                'test_cases': [
                    {'input': '3\nAli 901234567\nVali 901111111\nGani 902222222\n2\nAli\nBobur', 'output': '901234567\nTopilmadi', 'is_sample': True, 'order': 1},
                    {'input': '1\nTest 123\n1\nTest', 'output': '123', 'is_sample': True, 'order': 2},
                    {'input': '2\nA 111\nB 222\n3\nA\nB\nC', 'output': '111\n222\nTopilmadi', 'is_sample': False, 'order': 3},
                ],
            },

            # ═══════════════════════════════════════════
            # def — Funksiyalar (23-27)
            # ═══════════════════════════════════════════
            {
                'title': 'Faktorial',
                'slug': 'faktorial',
                'description': 'Musbat butun son berilgan. Uning faktorialini (n!) toping.',
                'input_format': 'Bitta son <code>n</code>.',
                'output_format': '<code>n!</code> ni chiqaring.',
                'constraints': '0 ≤ n ≤ 20',
                'difficulty': 'easy',
                'category_slug': 'def',
                'order': 23,
                'time_limit': 1,
                'starter_code': {'python': 'def factorial(n):\n    pass\n\nn = int(input())\nprint(factorial(n))'},
                'languages': 'all',
                'test_cases': [
                    {'input': '5', 'output': '120', 'is_sample': True, 'order': 1},
                    {'input': '0', 'output': '1', 'is_sample': True, 'order': 2},
                    {'input': '1', 'output': '1', 'is_sample': False, 'order': 3},
                    {'input': '10', 'output': '3628800', 'is_sample': False, 'order': 4},
                    {'input': '20', 'output': '2432902008176640000', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Fibonacci sonlari',
                'slug': 'fibonacci-sonlari',
                'description': 'N-chi Fibonacci sonini toping. F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2).',
                'input_format': 'Bitta son <code>n</code>.',
                'output_format': 'N-chi Fibonacci sonini chiqaring.',
                'constraints': '0 ≤ n ≤ 40',
                'difficulty': 'easy',
                'category_slug': 'def',
                'order': 24,
                'time_limit': 1,
                'starter_code': {'python': 'def fibonacci(n):\n    pass\n\nn = int(input())\nprint(fibonacci(n))'},
                'languages': 'all',
                'test_cases': [
                    {'input': '6', 'output': '8', 'is_sample': True, 'order': 1},
                    {'input': '0', 'output': '0', 'is_sample': True, 'order': 2},
                    {'input': '1', 'output': '1', 'is_sample': False, 'order': 3},
                    {'input': '10', 'output': '55', 'is_sample': False, 'order': 4},
                    {'input': '40', 'output': '102334155', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'Tub son tekshirish',
                'slug': 'tub-son-tekshirish',
                'description': 'Son berilgan. U tub (prime) yoki yo\'qligini aniqlang. Tub son — faqat 1 ga va o\'ziga bo\'linadigan son.',
                'input_format': 'Bitta son <code>n</code>.',
                'output_format': 'Tub bo\'lsa <code>HA</code>, aks holda <code>YOQ</code>.',
                'constraints': '1 ≤ n ≤ 10<sup>9</sup>',
                'difficulty': 'medium',
                'category_slug': 'def',
                'order': 25,
                'time_limit': 1,
                'starter_code': {'python': 'def is_prime(n):\n    pass\n\nn = int(input())\nprint("HA" if is_prime(n) else "YOQ")'},
                'languages': 'all',
                'test_cases': [
                    {'input': '7', 'output': 'HA', 'is_sample': True, 'order': 1},
                    {'input': '4', 'output': 'YOQ', 'is_sample': True, 'order': 2},
                    {'input': '1', 'output': 'YOQ', 'is_sample': False, 'order': 3},
                    {'input': '2', 'output': 'HA', 'is_sample': False, 'order': 4},
                    {'input': '97', 'output': 'HA', 'is_sample': False, 'order': 5},
                    {'input': '100', 'output': 'YOQ', 'is_sample': False, 'order': 6},
                    {'input': '999999937', 'output': 'HA', 'is_sample': False, 'order': 7},
                ],
            },
            {
                'title': 'Sonni so\'zga aylantirish',
                'slug': 'sonni-sozga-aylantirish',
                'description': 'Bir xonali son (0-9) berilgan. Uni o\'zbek tilida so\'z bilan chiqaring.',
                'input_format': 'Bitta son <code>n</code> (0-9).',
                'output_format': 'Sonni so\'z bilan chiqaring.',
                'constraints': '0 ≤ n ≤ 9',
                'difficulty': 'easy',
                'category_slug': 'def',
                'order': 26,
                'time_limit': 1,
                'starter_code': {'python': 'def son_sozda(n):\n    pass\n\nn = int(input())\nprint(son_sozda(n))'},
                'languages': 'python',
                'test_cases': [
                    {'input': '0', 'output': 'nol', 'is_sample': True, 'order': 1},
                    {'input': '5', 'output': 'besh', 'is_sample': True, 'order': 2},
                    {'input': '1', 'output': 'bir', 'is_sample': False, 'order': 3},
                    {'input': '2', 'output': 'ikki', 'is_sample': False, 'order': 4},
                    {'input': '3', 'output': 'uch', 'is_sample': False, 'order': 5},
                    {'input': '4', 'output': 'tort', 'is_sample': False, 'order': 6},
                    {'input': '6', 'output': 'olti', 'is_sample': False, 'order': 7},
                    {'input': '7', 'output': 'yetti', 'is_sample': False, 'order': 8},
                    {'input': '8', 'output': 'sakkiz', 'is_sample': False, 'order': 9},
                    {'input': '9', 'output': 'toqqiz', 'is_sample': False, 'order': 10},
                ],
            },
            {
                'title': 'EKUBni topish',
                'slug': 'ekubni-topish',
                'description': 'Ikki son berilgan. Ularning eng katta umumiy bo\'luvchisini (EKUB/GCD) toping.',
                'input_format': 'Bitta qatorda ikki musbat son <code>a</code> va <code>b</code>.',
                'output_format': 'EKUB ni chiqaring.',
                'constraints': '1 ≤ a, b ≤ 10<sup>9</sup>',
                'difficulty': 'medium',
                'category_slug': 'def',
                'order': 27,
                'time_limit': 1,
                'starter_code': {'python': 'def gcd(a, b):\n    pass\n\na, b = map(int, input().split())\nprint(gcd(a, b))'},
                'languages': 'all',
                'test_cases': [
                    {'input': '12 8', 'output': '4', 'is_sample': True, 'order': 1},
                    {'input': '7 3', 'output': '1', 'is_sample': True, 'order': 2},
                    {'input': '100 100', 'output': '100', 'is_sample': False, 'order': 3},
                    {'input': '1 1000000000', 'output': '1', 'is_sample': False, 'order': 4},
                    {'input': '48 36', 'output': '12', 'is_sample': False, 'order': 5},
                ],
            },

            # ═══════════════════════════════════════════
            # Sorting (28-29)
            # ═══════════════════════════════════════════
            {
                'title': 'Ro\'yxatni tartiblash',
                'slug': 'royxatni-tartiblash',
                'description': 'Butun sonlar ro\'yxati berilgan. Uni o\'sish tartibida tartiblang.',
                'input_format': 'Birinchi qatorda <code>n</code>. Ikkinchi qatorda <code>n</code> ta son.',
                'output_format': 'O\'sish tartibida, bo\'sh joy bilan chiqaring.',
                'constraints': '1 ≤ n ≤ 10<sup>5</sup>',
                'difficulty': 'easy',
                'category_slug': 'sorting',
                'order': 28,
                'time_limit': 2,
                'starter_code': {'python': 'n = int(input())\nnums = list(map(int, input().split()))\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '5\n5 3 1 4 2', 'output': '1 2 3 4 5', 'is_sample': True, 'order': 1},
                    {'input': '3\n-1 -3 -2', 'output': '-3 -2 -1', 'is_sample': True, 'order': 2},
                    {'input': '1\n42', 'output': '42', 'is_sample': False, 'order': 3},
                    {'input': '4\n1 1 1 1', 'output': '1 1 1 1', 'is_sample': False, 'order': 4},
                    {'input': '6\n3 -1 4 -1 5 -9', 'output': '-9 -1 -1 3 4 5', 'is_sample': False, 'order': 5},
                ],
            },
            {
                'title': 'K-chi eng kichik element',
                'slug': 'k-chi-eng-kichik-element',
                'description': 'Butun sonlar ro\'yxati va <code>k</code> soni berilgan. K-chi eng kichik elementni toping.',
                'input_format': 'Birinchi qatorda <code>n</code> va <code>k</code>. Ikkinchi qatorda <code>n</code> ta son.',
                'output_format': 'K-chi eng kichik elementni chiqaring.',
                'constraints': '1 ≤ k ≤ n ≤ 10<sup>5</sup>',
                'difficulty': 'medium',
                'category_slug': 'sorting',
                'order': 29,
                'time_limit': 2,
                'starter_code': {'python': 'n, k = map(int, input().split())\nnums = list(map(int, input().split()))\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '5 3\n5 3 1 4 2', 'output': '3', 'is_sample': True, 'order': 1},
                    {'input': '3 1\n10 20 30', 'output': '10', 'is_sample': True, 'order': 2},
                    {'input': '4 4\n1 2 3 4', 'output': '4', 'is_sample': False, 'order': 3},
                    {'input': '5 2\n-5 -3 -1 0 2', 'output': '-3', 'is_sample': False, 'order': 4},
                    {'input': '3 2\n5 5 5', 'output': '5', 'is_sample': False, 'order': 5},
                ],
            },

            # ═══════════════════════════════════════════
            # Math (30)
            # ═══════════════════════════════════════════
            {
                'title': 'Sonlar o\'rtachasi',
                'slug': 'sonlar-ortachasi',
                'description': 'N ta son berilgan. Ularning o\'rtacha qiymatini (arifmetik o\'rta) toping.',
                'input_format': 'Birinchi qatorda <code>n</code>. Ikkinchi qatorda <code>n</code> ta son.',
                'output_format': 'O\'rtacha qiymatni 2 kasr raqam bilan chiqaring.',
                'constraints': '1 ≤ n ≤ 10<sup>5</sup>',
                'difficulty': 'easy',
                'category_slug': 'math',
                'order': 30,
                'time_limit': 1,
                'starter_code': {'python': 'n = int(input())\nnums = list(map(int, input().split()))\n'},
                'languages': 'all',
                'test_cases': [
                    {'input': '4\n10 20 30 40', 'output': '25.00', 'is_sample': True, 'order': 1},
                    {'input': '3\n1 2 3', 'output': '2.00', 'is_sample': True, 'order': 2},
                    {'input': '1\n5', 'output': '5.00', 'is_sample': False, 'order': 3},
                    {'input': '2\n-10 10', 'output': '0.00', 'is_sample': False, 'order': 4},
                    {'input': '3\n1 1 2', 'output': '1.33', 'is_sample': False, 'order': 5},
                ],
            },
        ]

        created_count = 0
        for p_data in problems_data:
            if CodingProblem.objects.filter(slug=p_data['slug']).exists():
                self.stdout.write(f"  ~ {p_data['title']} (mavjud)")
                continue

            category = CodingCategory.objects.get(slug=p_data['category_slug'])

            problem = CodingProblem.objects.create(
                title=p_data['title'],
                slug=p_data['slug'],
                description=p_data['description'],
                input_format=p_data['input_format'],
                output_format=p_data['output_format'],
                constraints=p_data.get('constraints', ''),
                difficulty=p_data['difficulty'],
                category=category,
                starter_code=p_data.get('starter_code', {}),
                time_limit=p_data.get('time_limit', 2),
                memory_limit=p_data.get('memory_limit', 256),
                order=p_data['order'],
                is_active=True,
            )

            # Tillarni bog'lash
            if p_data.get('languages') == 'all':
                problem.languages.set(all_langs)
            elif p_data.get('languages') == 'python':
                problem.languages.set([python])
            else:
                problem.languages.set(all_langs)

            # Test case'lar
            for tc in p_data['test_cases']:
                TestCase.objects.create(
                    problem=problem,
                    input_data=tc['input'],
                    expected_output=tc['output'],
                    is_sample=tc['is_sample'],
                    order=tc['order'],
                )

            created_count += 1
            self.stdout.write(f"  ✓ #{p_data['order']} {p_data['title']} ({len(p_data['test_cases'])} test)")

        self.stdout.write(self.style.SUCCESS(f"\n  {created_count} masala yaratildi!"))

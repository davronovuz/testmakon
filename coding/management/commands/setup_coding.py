"""
TestMakon.uz — Boshlang'ich dasturlash tillari va kategoriyalarni yaratish
Usage: python manage.py setup_coding
"""

from django.core.management.base import BaseCommand
from coding.models import ProgrammingLanguage, CodingCategory


class Command(BaseCommand):
    help = "Dasturlash tillari va kategoriyalarni yaratish"

    def handle(self, *args, **options):
        # === Tillar ===
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

        for lang_data in languages:
            obj, created = ProgrammingLanguage.objects.update_or_create(
                slug=lang_data['slug'],
                defaults=lang_data,
            )
            status = "yaratildi" if created else "yangilandi"
            self.stdout.write(f"  {obj.name} — {status}")

        # === Kategoriyalar ===
        categories = [
            {'name': 'Array', 'slug': 'array', 'icon': 'bi-list-ol', 'order': 1},
            {'name': 'String', 'slug': 'string', 'icon': 'bi-fonts', 'order': 2},
            {'name': 'Math', 'slug': 'math', 'icon': 'bi-calculator', 'order': 3},
            {'name': 'Sorting', 'slug': 'sorting', 'icon': 'bi-sort-down', 'order': 4},
            {'name': 'Recursion', 'slug': 'recursion', 'icon': 'bi-arrow-repeat', 'order': 5},
            {'name': 'Dynamic Programming', 'slug': 'dp', 'icon': 'bi-grid-3x3', 'order': 6},
        ]

        for cat_data in categories:
            obj, created = CodingCategory.objects.update_or_create(
                slug=cat_data['slug'],
                defaults=cat_data,
            )
            status = "yaratildi" if created else "yangilandi"
            self.stdout.write(f"  {obj.name} — {status}")

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ {len(languages)} til + {len(categories)} kategoriya tayyor!"
        ))

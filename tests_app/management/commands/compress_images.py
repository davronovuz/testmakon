"""
Barcha Subject rasmlarini kichraytirish (400x400 max, quality=85)
Ishlatish: python manage.py compress_images
"""
from django.core.management.base import BaseCommand
from tests_app.models import Subject
from PIL import Image


class Command(BaseCommand):
    help = "Subject rasmlarini 400x400 ga kichraytiradi"

    def handle(self, *args, **options):
        subjects = Subject.objects.filter(image__isnull=False).exclude(image='')
        count = 0
        for s in subjects:
            try:
                img = Image.open(s.image.path)
                if img.width > 400 or img.height > 400:
                    img.thumbnail((400, 400), Image.LANCZOS)
                    img.save(s.image.path, optimize=True, quality=85)
                    count += 1
                    self.stdout.write(f"  OK: {s.name}")
            except Exception as e:
                self.stdout.write(f"  SKIP {s.name}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Tayyor: {count} ta rasm kichraytirildi"))

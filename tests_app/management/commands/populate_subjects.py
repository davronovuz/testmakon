"""
DTM fanlarini bazaga qo'shish.
Usage: python manage.py populate_subjects
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from tests_app.models import Subject


class Command(BaseCommand):
    help = "DTM fanlarini bazaga qo'shadi"

    SUBJECTS = [
        {"name": "Matematika", "icon": "📐", "color": "#3B82F6", "order": 1},
        {"name": "Fizika", "icon": "⚛️", "color": "#8B5CF6", "order": 2},
        {"name": "Kimyo", "icon": "🧪", "color": "#10B981", "order": 3},
        {"name": "Biologiya", "icon": "🧬", "color": "#059669", "order": 4},
        {"name": "Ona tili va adabiyot", "icon": "📚", "color": "#F59E0B", "order": 5},
        {"name": "Ingliz tili", "icon": "🇬🇧", "color": "#EF4444", "order": 6},
        {"name": "Tarix", "icon": "🏛️", "color": "#D97706", "order": 7},
        {"name": "Geografiya", "icon": "🌍", "color": "#14B8A6", "order": 8},
        {"name": "Informatika", "icon": "💻", "color": "#6366F1", "order": 9},
        {"name": "Huquqshunoslik", "icon": "⚖️", "color": "#EC4899", "order": 10},
        {"name": "Iqtisodiyot", "icon": "📊", "color": "#F97316", "order": 11},
        {"name": "Rus tili", "icon": "🇷🇺", "color": "#EF4444", "order": 12},
        {"name": "Nemis tili", "icon": "🇩🇪", "color": "#EAB308", "order": 13},
        {"name": "Fransuz tili", "icon": "🇫🇷", "color": "#3B82F6", "order": 14},
    ]

    def handle(self, *args, **options):
        created = 0
        for s in self.SUBJECTS:
            slug = slugify(s["name"])
            _, c = Subject.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": s["name"],
                    "icon": s["icon"],
                    "color": s["color"],
                    "order": s["order"],
                    "is_active": True,
                },
            )
            if c:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  + {s['name']}"))
            else:
                self.stdout.write(f"  ~ {s['name']} (mavjud)")

        self.stdout.write(self.style.SUCCESS(f"\nTayyor! {created} ta fan qo'shildi."))

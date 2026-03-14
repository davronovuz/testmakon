"""
Milliy Sertifikat savollarini JSON fayldan import qilish.

Ishlatish:
    python manage.py import_cert_questions --file savollar.json

JSON format namunasi: sample_cert_questions.json
"""
import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from certificate.models import (
    CertSubject, CertMock, CertQuestion,
    CertChoice, CertGroupedOption, CertGroupedItem,
    CertShortOpen, CertMultiPart
)
from tests_app.models import Subject


class Command(BaseCommand):
    help = 'JSON fayldan Milliy Sertifikat savollarini import qilish'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='JSON fayl yo\'li')
        parser.add_argument('--update', action='store_true', help='Mavjud savollarni yangilash')
        parser.add_argument('--dry-run', action='store_true', help='Amalda saqlamasdan tekshirish')

    def handle(self, *args, **options):
        filepath = options['file']
        do_update = options['update']
        dry_run = options['dry_run']

        try:
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"Fayl topilmadi: {filepath}")
        except json.JSONDecodeError as e:
            raise CommandError(f"JSON xatosi: {e}")

        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE (hech narsa saqlanmaydi) ---"))

        mocks_data = data if isinstance(data, list) else [data]

        for mock_data in mocks_data:
            try:
                with transaction.atomic():
                    self._import_mock(mock_data, do_update, dry_run)
                    if dry_run:
                        raise Exception("dry-run rollback")
            except Exception as e:
                if dry_run and "dry-run rollback" in str(e):
                    pass
                else:
                    self.stdout.write(self.style.ERROR(f"Xato: {e}"))

        self.stdout.write(self.style.SUCCESS("Import yakunlandi!"))

    def _import_mock(self, data, do_update, dry_run):
        # 1. Fan
        subject_slug = data.get('subject_slug') or data.get('subject')
        try:
            subject = Subject.objects.get(slug=subject_slug)
        except Subject.DoesNotExist:
            raise CommandError(f"Fan topilmadi: '{subject_slug}'. Avval admin panelda Subject yarating.")

        cert_subject, _ = CertSubject.objects.get_or_create(
            subject=subject,
            defaults={'is_active': True, 'order': 0}
        )

        # 2. Mock
        mock_slug = data.get('mock_slug') or data.get('slug')
        mock_title = data.get('mock_title') or data.get('title', 'Mock')

        if do_update:
            mock, created = CertMock.objects.update_or_create(
                cert_subject=cert_subject, slug=mock_slug,
                defaults={
                    'title': mock_title,
                    'year': data.get('year'),
                    'version': data.get('version', ''),
                    'time_limit': data.get('time_limit', 150),
                    'is_free': data.get('is_free', True),
                    'is_active': True,
                }
            )
        else:
            mock, created = CertMock.objects.get_or_create(
                cert_subject=cert_subject, slug=mock_slug,
                defaults={
                    'title': mock_title,
                    'year': data.get('year'),
                    'version': data.get('version', ''),
                    'time_limit': data.get('time_limit', 150),
                    'is_free': data.get('is_free', True),
                    'is_active': True,
                }
            )

        action = "Yaratildi" if created else "Mavjud"
        self.stdout.write(f"  Mock: [{action}] {mock}")

        # 3. Questions
        questions = data.get('questions', [])
        created_q = 0
        skipped_q = 0

        for q_data in questions:
            number = q_data.get('number')
            qtype = q_data.get('type')

            if not number or not qtype:
                self.stdout.write(self.style.WARNING(f"    Savol #{number}: type yoki number yo'q, o'tkazildi"))
                skipped_q += 1
                continue

            # Question
            q_defaults = {
                'question_type': qtype,
                'text': q_data.get('text', ''),
                'points': q_data.get('points', 1),
                'explanation': q_data.get('explanation', ''),
                'hint': q_data.get('hint', ''),
                'source': q_data.get('source', ''),
                'year': q_data.get('year'),
                'is_active': True,
            }

            if do_update:
                q, q_created = CertQuestion.objects.update_or_create(
                    mock=mock, number=number, defaults=q_defaults
                )
            else:
                q, q_created = CertQuestion.objects.get_or_create(
                    mock=mock, number=number, defaults=q_defaults
                )

            if not q_created and not do_update:
                skipped_q += 1
                continue

            # Clear old detail data if updating
            if do_update and not q_created:
                q.choices.all().delete()
                q.grouped_options.all().delete()
                q.grouped_items.all().delete()
                CertShortOpen.objects.filter(question=q).delete()
                q.parts.all().delete()

            # Type-specific data
            if qtype == 'choice':
                self._import_choice(q, q_data)
            elif qtype == 'grouped_af':
                self._import_grouped_af(q, q_data)
            elif qtype == 'short_open':
                self._import_short_open(q, q_data)
            elif qtype == 'multi_part':
                self._import_multi_part(q, q_data)

            created_q += 1

        # Update cached stats
        mock.update_cached_stats()
        cert_subject.update_stats()

        self.stdout.write(
            self.style.SUCCESS(f"    Savollar: {created_q} qo'shildi, {skipped_q} o'tkazildi")
        )

    def _import_choice(self, q, data):
        for opt in data.get('choices', []):
            CertChoice.objects.create(
                question=q,
                label=opt.get('label', 'A'),
                text=opt.get('text', ''),
                is_correct=opt.get('is_correct', False),
                order=opt.get('order', 0),
            )

    def _import_grouped_af(self, q, data):
        option_map = {}
        for opt in data.get('options', []):
            obj = CertGroupedOption.objects.create(
                question=q,
                label=opt.get('label', 'A'),
                text=opt.get('text', ''),
                order=opt.get('order', 0),
            )
            option_map[opt.get('label')] = obj

        for item in data.get('items', []):
            correct_label = item.get('correct_option')
            correct_obj = option_map.get(correct_label)
            CertGroupedItem.objects.create(
                question=q,
                item_number=item.get('number', 1),
                text=item.get('text', ''),
                correct_option=correct_obj,
            )

    def _import_short_open(self, q, data):
        ans = data.get('answer', {})
        CertShortOpen.objects.create(
            question=q,
            correct_answer=str(ans.get('value', '')),
            answer_type=ans.get('type', 'text'),
            tolerance=ans.get('tolerance', 0.0),
            case_sensitive=ans.get('case_sensitive', False),
        )

    def _import_multi_part(self, q, data):
        for i, part in enumerate(data.get('parts', [])):
            CertMultiPart.objects.create(
                question=q,
                part_label=part.get('label', chr(97+i)),
                text=part.get('text', ''),
                points=part.get('points', 1),
                correct_answer=str(part.get('answer', '')),
                answer_type=part.get('answer_type', 'text'),
                requires_manual_check=part.get('manual_check', False),
                tolerance=part.get('tolerance', 0.0),
                order=i,
            )

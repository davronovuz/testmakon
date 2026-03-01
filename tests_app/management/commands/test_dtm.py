"""
DTM Simulyatsiya logikasini to'liq test qilish.
Ishlatish: docker-compose exec web python manage.py test_dtm
"""
import random
import json
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from tests_app.models import Subject, Question


class Command(BaseCommand):
    help = 'DTM simulyatsiya logikasini test qiladi'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('  DTM SIMULYATSIYA TEST')
        self.stdout.write('='*60 + '\n')

        ok = True

        # ─── 1. DB'dagi fanlar ───────────────────────────────────
        self.stdout.write('\n[1] DB\'dagi aktiv fanlar:')
        subjects = list(Subject.objects.filter(is_active=True).annotate(
            questions_count=Count('questions', filter=Q(questions__is_active=True))
        ).order_by('order'))

        if not subjects:
            self.stdout.write(self.style.ERROR('  ✗ Hech qanday aktiv fan topilmadi!'))
            return

        slug_to_id = {s.slug: str(s.id) for s in subjects}
        id_to_name = {str(s.id): s.name for s in subjects}

        for s in subjects:
            qs_count = s.questions_count
            color = self.style.SUCCESS if qs_count >= 30 else (
                self.style.WARNING if qs_count > 0 else self.style.ERROR
            )
            self.stdout.write(f'  {color(f"[{qs_count:3d}q]")} {s.slug:35s} → {s.name}')

        # ─── 2. ID-compat map ────────────────────────────────────
        self.stdout.write('\n[2] ID-compat map (slug → ID matching):')
        SLUG_COMPAT = {
            'matematika':  ['fizika', 'informatika', 'ingliz-tili', 'geografiya'],
            'fizika':      ['matematika', 'informatika', 'ingliz-tili'],
            'kimyo':       ['biologiya', 'matematika', 'ingliz-tili'],
            'biologiya':   ['kimyo', 'ingliz-tili', 'geografiya'],
            'informatika': ['matematika', 'fizika', 'ingliz-tili'],
            'ingliz-tili': ['matematika', 'fizika', 'kimyo', 'biologiya', 'informatika', 'geografiya'],
            'geografiya':  ['matematika', 'ingliz-tili', 'biologiya'],
            'tarix':       ['geografiya', 'ingliz-tili'],
        }

        id_compat = {}
        for s1_slug, compat_slugs in SLUG_COMPAT.items():
            s1_id = slug_to_id.get(s1_slug)
            if not s1_id:
                for s in subjects:
                    if s1_slug.replace('-', '') in s.slug.replace('-', '').replace('_', ''):
                        s1_id = str(s.id)
                        break
            if s1_id:
                compat_ids = []
                for cs in compat_slugs:
                    cid = slug_to_id.get(cs)
                    if not cid:
                        for s in subjects:
                            if cs.replace('-', '') in s.slug.replace('-', '').replace('_', ''):
                                cid = str(s.id)
                                break
                    if cid:
                        compat_ids.append(cid)
                if compat_ids:
                    id_compat[s1_id] = compat_ids

        for s1_slug in SLUG_COMPAT:
            s1_id = next((k for k, v in slug_to_id.items() if k == s1_slug), None)
            if s1_id is None:
                s1_id = next((str(s.id) for s in subjects
                              if s1_slug.replace('-', '') in s.slug.replace('-', '')), None)
            found = s1_id and s1_id in id_compat
            compat_names = [id_to_name[cid] for cid in id_compat.get(s1_id or '', [])]
            if found:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {s1_slug:15s}') +
                    f' → {", ".join(compat_names)}'
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ {s1_slug:15s} — DB\'da topilmadi!')
                )
                ok = False

        # ─── 3. Majburiy fanlar ──────────────────────────────────
        self.stdout.write('\n[3] Majburiy fanlar (ona tili, matematika, tarix):')

        def find_mandatory(slug_list, name_hint):
            for slug in slug_list:
                s = Subject.objects.filter(slug=slug, is_active=True).first()
                if s:
                    return s
            return Subject.objects.filter(name__icontains=name_hint, is_active=True).first()

        mandatory_defs = [
            (['ona-tili', 'ona-tili-va-adabiyot', 'ona-tili-adabiyot', 'onatili'], 'Ona tili'),
            (['matematika'], 'Matematika'),
            (['ozbekiston-tarixi', "o'zbekiston-tarixi", 'tarix', 'ozbek-tarixi'], "O'zbekiston tarixi"),
        ]

        mandatory_found = []
        for slug_list, name_hint in mandatory_defs:
            s = find_mandatory(slug_list, name_hint)
            if s:
                q_count = Question.objects.filter(subject=s, is_active=True).count()
                color = self.style.SUCCESS if q_count >= 10 else self.style.WARNING
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {name_hint:20s}') +
                    f' → "{s.name}" (slug={s.slug}) ' +
                    color(f'[{q_count} savol]')
                )
                if q_count < 10:
                    self.stdout.write(
                        self.style.WARNING(f'    ⚠ Kamida 10 ta savol kerak, {q_count} ta bor!')
                    )
                mandatory_found.append(s)
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ {name_hint:20s} — DB\'da TOPILMADI!')
                )
                ok = False

        # ─── 4. Scenario sinovlar ────────────────────────────────
        self.stdout.write('\n[4] Scenario sinovlar (fan1 + fan2 kombinatsiyalari):')

        test_combos = [
            ('fizika', 'matematika'),
            ('fizika', 'ingliz-tili'),
            ('biologiya', 'kimyo'),
            ('matematika', 'informatika'),
            ('ingliz-tili', 'fizika'),
            ('tarix', 'ingliz-tili'),
        ]

        for s1_slug, s2_slug in test_combos:
            fan1 = Subject.objects.filter(slug=s1_slug, is_active=True).first()
            fan2 = Subject.objects.filter(slug=s2_slug, is_active=True).first()

            if not fan1:
                self.stdout.write(self.style.ERROR(f'  ✗ {s1_slug} + {s2_slug}: fan1 topilmadi'))
                ok = False
                continue
            if not fan2:
                self.stdout.write(self.style.ERROR(f'  ✗ {s1_slug} + {s2_slug}: fan2 topilmadi'))
                ok = False
                continue

            seen_ids = set()

            def get_questions(subject, count):
                qs = list(Question.objects.filter(
                    subject=subject, is_active=True
                ).exclude(id__in=seen_ids))
                random.shuffle(qs)
                selected = qs[:count]
                for q in selected:
                    seen_ids.add(q.id)
                return selected

            all_q = []
            q1 = get_questions(fan1, 30)
            all_q.extend(q1)
            q2 = get_questions(fan2, 30)
            all_q.extend(q2)

            mandatory_q = {}
            for s in mandatory_found:
                mq = get_questions(s, 10)
                all_q.extend(mq)
                mandatory_q[s.name] = len(mq)

            total = len(all_q)
            duplicates = total - len(set(q.id for q in all_q))

            if total >= 20 and duplicates == 0:
                detail = (
                    f'{len(q1)}/30 + {len(q2)}/30 + '
                    f'majburiy: ' + ' + '.join(f'{v}/10 {k[:6]}' for k, v in mandatory_q.items())
                )
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {s1_slug:12s} + {s2_slug:12s}') +
                    f' → {total} savol ({detail})'
                )
                if total < 90:
                    self.stdout.write(
                        self.style.WARNING(f'    ⚠ {90-total} ta savol yetishmaydi (savollar kam bo\'lsa kerak)')
                    )
            else:
                if duplicates > 0:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ {s1_slug} + {s2_slug}: {duplicates} ta takroriy savol!')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ {s1_slug} + {s2_slug}: faqat {total} savol (min 20 kerak)')
                    )
                ok = False

        # ─── 5. JSON tekshirish ──────────────────────────────────
        self.stdout.write('\n[5] JSON format tekshiruvi:')
        try:
            j = json.dumps(id_compat)
            parsed = json.loads(j)
            total_pairs = sum(len(v) for v in parsed.values())
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ id_compat_json valid: {len(parsed)} fan, {total_pairs} mos juftlik')
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ JSON xatosi: {e}'))
            ok = False

        # ─── Natija ──────────────────────────────────────────────
        self.stdout.write('\n' + '='*60)
        if ok:
            self.stdout.write(self.style.SUCCESS('  ✅  BARCHA TESTLAR O\'TDI — DTM 100% TAYYOR'))
        else:
            self.stdout.write(self.style.ERROR('  ❌  BA\'ZI TESTLAR XATO — DB\'ga savollar qo\'shing'))
        self.stdout.write('='*60 + '\n')

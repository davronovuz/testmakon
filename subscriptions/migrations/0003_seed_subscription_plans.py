from django.db import migrations


def create_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')

    # Avval bor bo'lsa o'chirmaymiz, yo'q bo'lsa yaratamiz
    plans = [
        {
            'name': '1 Oylik Premium',
            'slug': 'premium-1-oy',
            'plan_type': 'premium',
            'price': 30000,
            'original_price': None,
            'duration_days': 30,
            'daily_test_limit': None,
            'can_access_analytics': True,
            'can_access_ai_mentor': True,
            'can_download_pdf': True,
            'can_access_competitions': True,
            'ad_free': True,
            'is_active': True,
            'is_featured': False,
            'order': 1,
            'features': ['Cheksiz testlar', 'AI Mentor', 'Shaxsiy tahlil', 'Reklama yoq'],
        },
        {
            'name': '3 Oylik Premium',
            'slug': 'premium-3-oy',
            'plan_type': 'premium',
            'price': 75000,
            'original_price': 90000,
            'duration_days': 90,
            'daily_test_limit': None,
            'can_access_analytics': True,
            'can_access_ai_mentor': True,
            'can_download_pdf': True,
            'can_access_competitions': True,
            'ad_free': True,
            'is_active': True,
            'is_featured': True,
            'order': 2,
            'features': ['Cheksiz testlar', 'AI Mentor', 'Shaxsiy tahlil', 'Reklama yoq', 'DTM simulyatsiya'],
        },
        {
            'name': '6 Oylik Premium',
            'slug': 'premium-6-oy',
            'plan_type': 'premium',
            'price': 135000,
            'original_price': 180000,
            'duration_days': 180,
            'daily_test_limit': None,
            'can_access_analytics': True,
            'can_access_ai_mentor': True,
            'can_download_pdf': True,
            'can_access_competitions': True,
            'ad_free': True,
            'is_active': True,
            'is_featured': False,
            'order': 3,
            'features': ['Cheksiz testlar', 'AI Mentor', 'Shaxsiy tahlil', 'Reklama yoq', 'DTM simulyatsiya', 'Sertifikat PDF'],
        },
    ]

    for plan_data in plans:
        SubscriptionPlan.objects.get_or_create(
            slug=plan_data['slug'],
            defaults=plan_data,
        )


def delete_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')
    SubscriptionPlan.objects.filter(
        slug__in=['premium-1-oy', 'premium-3-oy', 'premium-6-oy']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_payment_receipt_image'),
    ]

    operations = [
        migrations.RunPython(create_plans, delete_plans),
    ]

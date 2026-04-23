"""
Battle modeliga Ready phase fieldlari:
  - challenger_ready, opponent_ready (default False)
  - ready_expires_at (null=True)

Matchmaking flow: match topilgach avtomatik testga kirmaydi,
oldin ikkala user "Tayyorman" bosishi kerak.

Backward-compatible: barcha mavjud Battle rows-ga default qiymatlar qo'yiladi.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0006_remove_unique_date_dailychallenge'),
    ]

    operations = [
        migrations.AddField(
            model_name='battle',
            name='challenger_ready',
            field=models.BooleanField(default=False, verbose_name='Chaqiruvchi tayyor'),
        ),
        migrations.AddField(
            model_name='battle',
            name='opponent_ready',
            field=models.BooleanField(default=False, verbose_name='Raqib tayyor'),
        ),
        migrations.AddField(
            model_name='battle',
            name='ready_expires_at',
            field=models.DateTimeField(
                blank=True, null=True,
                help_text="Bu vaqtgacha ikkala user tayyor bo'lmasa battle bekor qilinadi",
                verbose_name='Tayyorgarlik muddati',
            ),
        ),
    ]

"""
TestMakon.uz — Google OAuth integratsiyasi uchun migration.
Ikki yangi nullable field qo'shadi:
  - google_id (unique, indexed) — Google foydalanuvchisini aniqlash uchun
  - google_photo_url — profil rasmi

Mavjud foydalanuvchilar uchun ikkala maydon ham NULL/bo'sh bo'ladi,
shuning uchun bu migration 100% backward-compatible va zero-downtime.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_user_rating_last_online'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='google_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=100,
                null=True,
                unique=True,
                verbose_name='Google ID',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='google_photo_url',
            field=models.URLField(
                blank=True,
                verbose_name='Google foto',
            ),
        ),
    ]

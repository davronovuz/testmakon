from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_telegramauthcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='rating',
            field=models.PositiveIntegerField(db_index=True, default=1000, verbose_name='Battle reytingi'),
        ),
        migrations.AddField(
            model_name='user',
            name='last_online',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Oxirgi online vaqt'),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_core', '0003_add_system_prompt_to_conversation'),
    ]

    operations = [
        migrations.AddField(
            model_name='studyplan',
            name='is_ai_generated',
            field=models.BooleanField(default=False, verbose_name='AI tomonidan tuzilgan'),
        ),
        migrations.AddField(
            model_name='studyplantask',
            name='ai_notes',
            field=models.TextField(blank=True, verbose_name='AI izohi'),
        ),
        migrations.AddField(
            model_name='studyplantask',
            name='difficulty',
            field=models.CharField(
                choices=[('easy', 'Oson'), ('medium', "O'rta"), ('hard', 'Qiyin')],
                default='medium',
                max_length=10,
                verbose_name='Qiyinlik'
            ),
        ),
        migrations.AddField(
            model_name='studyplantask',
            name='weak_topic_focus',
            field=models.BooleanField(default=False, verbose_name='Sust mavzu'),
        ),
    ]

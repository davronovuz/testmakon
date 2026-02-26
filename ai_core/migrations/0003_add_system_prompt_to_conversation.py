from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_core', '0002_add_questions_count_to_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiconversation',
            name='system_prompt',
            field=models.TextField(blank=True, verbose_name='System prompt'),
        ),
    ]

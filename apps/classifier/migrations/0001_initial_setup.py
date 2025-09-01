from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(default='Sem assunto', max_length=500)),
                ('content', models.TextField()),
                ('sender', models.EmailField(default='unknown@example.com')),
                ('sender_email', models.EmailField(blank=True, null=True)),
                ('classification_result', models.CharField(blank=True, choices=[('productive', 'Produtivo'), ('unproductive', 'Improdutivo'), ('neutral', 'Neutro')], max_length=20, null=True)),
                ('confidence_score', models.FloatField(blank=True, null=True)),
                ('reasoning', models.TextField(blank=True, null=True)),
                ('ai_model_used', models.CharField(default='huggingface-api', max_length=100)),
                ('model_used', models.CharField(default='huggingface-api', max_length=100)),
                ('processing_time_seconds', models.FloatField(default=0.0)),
                ('processing_time', models.FloatField(default=0.0)),
                ('processing_status', models.CharField(default='completed', max_length=20)),
                ('suggested_response', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('classified_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'emails',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='email',
            index=models.Index(fields=['classification_result'], name='emails_classification_result_idx'),
        ),
        migrations.AddIndex(
            model_name='email',
            index=models.Index(fields=['created_at'], name='emails_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='email',
            index=models.Index(fields=['confidence_score'], name='emails_confidence_score_idx'),
        ),
    ]

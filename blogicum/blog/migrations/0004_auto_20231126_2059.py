# Generated by Django 3.2.16 on 2023-11-26 15:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog', '0003_auto_20231116_1050'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Текст')),
                ('pub_date', models.DateTimeField(verbose_name='Дата и время публикации')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Автор публикации')),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='comments',
            field=models.ManyToManyField(to='blog.CommentModel'),
        ),
    ]
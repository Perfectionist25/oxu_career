from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="slug",
            field=models.SlugField(
                max_length=255,
                unique=True,
                verbose_name="Slug",
                help_text="URL-friendly identifier",
            ),
        ),
    ]

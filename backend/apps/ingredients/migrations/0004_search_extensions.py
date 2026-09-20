from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ingredients", "0003_ingredient_translations"),
    ]

    operations = [
        UnaccentExtension(),
        TrigramExtension(),
    ]

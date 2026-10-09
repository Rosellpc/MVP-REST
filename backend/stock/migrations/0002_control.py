from django.db import migrations


def seed(apps, schema_editor):
    apps.get_model("stock", "StockControl").objects.using(schema_editor.connection.alias).get_or_create(pk=1)


class Migration(migrations.Migration):
    dependencies = [("stock", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]

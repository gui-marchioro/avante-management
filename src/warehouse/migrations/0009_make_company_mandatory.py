# Generated manually on 2026-02-12

import django.db.models.deletion
from django.db import migrations, models


def backfill_company_relations(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    ItemType = apps.get_model("warehouse", "ItemType")
    Manufacturer = apps.get_model("warehouse", "Manufacturer")
    Item = apps.get_model("warehouse", "Item")

    fallback_company, _ = Company.objects.get_or_create(
        cnpj="00000000000000",
        defaults={"name": "Legacy Company", "is_active": False},
    )

    ItemType.objects.filter(company__isnull=True).update(company=fallback_company)
    Manufacturer.objects.filter(company__isnull=True).update(company=fallback_company)

    for item in Item.objects.filter(company__isnull=True).select_related("type", "manufacturer"):
        if item.type_id and item.type.company_id:
            item.company_id = item.type.company_id
        elif item.manufacturer_id and item.manufacturer.company_id:
            item.company_id = item.manufacturer.company_id
        else:
            item.company = fallback_company
        item.save(update_fields=["company"])


class Migration(migrations.Migration):

    dependencies = [
        ("warehouse", "0008_alter_item_options_alter_itemtype_options_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_company_relations, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="item",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="companies.company",
            ),
        ),
        migrations.AlterField(
            model_name="itemtype",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="item_types",
                to="companies.company",
            ),
        ),
        migrations.AlterField(
            model_name="manufacturer",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="manufacturers",
                to="companies.company",
            ),
        ),
    ]

# Generated manually on 2026-02-12

from django.db import migrations


def backfill_default_feature_and_admin_permission(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    Feature = apps.get_model("companies", "Feature")
    CompanyFeature = apps.get_model("companies", "CompanyFeature")

    companies_feature, _ = Feature.objects.get_or_create(
        code="companies",
        defaults={"name": "Companies", "is_active": True},
    )

    for company in Company.objects.all():
        CompanyFeature.objects.get_or_create(
            company=company,
            feature=companies_feature,
            defaults={"enabled": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0003_alter_company_options"),
    ]

    operations = [
        migrations.RunPython(
            backfill_default_feature_and_admin_permission,
            migrations.RunPython.noop,
        ),
    ]

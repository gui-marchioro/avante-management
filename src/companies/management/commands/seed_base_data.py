# python manage.py seed_base_data
from __future__ import annotations

from decimal import Decimal
from typing import TypedDict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand

from companies.models import Company, CompanyFeature, Employee, Feature
from warehouse.models import Item, ItemType, Manufacturer


User = get_user_model()


class SeedItem(TypedDict):
    name: str
    type_name: str
    manufacturer_name: str
    model: str
    quantity: int
    market_value: str
    description: str


class SeedCompany(TypedDict):
    name: str
    cnpj: str
    owner_username: str
    owner_email: str
    owner_password: str
    item_types: list[str]
    manufacturers: list[str]
    items: list[SeedItem]
    enabled_features: list[str]


SEED_DATA: list[SeedCompany] = [
    {
        "name": "Avante Industrial",
        "cnpj": "12345678000199",
        "owner_username": "avante_admin",
        "owner_email": "avante_admin@example.com",
        "owner_password": "avante_admin",
        "item_types": ["PLC", "HMI", "Sensor", "Inversor"],
        "manufacturers": ["Siemens", "Schneider", "WEG"],
        "enabled_features": ["companies", "warehouse"],
        "items": [
            {
                "name": "S7-200",
                "type_name": "PLC",
                "manufacturer_name": "Siemens",
                "model": "S7-200",
                "quantity": 4,
                "market_value": "500.00",
                "description": "",
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Populate base data for companies and warehouse apps."

    def add_arguments(self, parser):
        parser.add_argument(
            "--owner-password",
            dest="owner_password",
            help="Override default owner password for all created owners.",
        )

    def handle(self, *args, **options):
        override_password: str | None = options.get("owner_password")
        warehouse_permissions = list(
            Permission.objects.filter(content_type__app_label="warehouse")
        )
        add_employee_permission = Permission.objects.get(
            content_type__app_label="companies",
            codename="add_employee",
        )
        manage_features_permission = Permission.objects.get(
            content_type__app_label="companies",
            codename="manage_company_features",
        )

        for company_seed in SEED_DATA:
            company, company_created = Company.objects.get_or_create(
                cnpj=company_seed["cnpj"],
                defaults={"name": company_seed["name"], "is_active": True},
            )
            if not company_created and company.name != company_seed["name"]:
                company.name = company_seed["name"]
                company.save(update_fields=["name"])

            password = override_password or company_seed["owner_password"]
            owner, owner_created = User.objects.get_or_create(
                username=company_seed["owner_username"],
                defaults={
                    "email": company_seed["owner_email"],
                    "first_name": "Tenant",
                    "last_name": "Admin",
                },
            )
            if owner_created:
                owner.set_password(password)
                owner.save(update_fields=["password"])
            if not owner_created and override_password:
                owner.set_password(password)
                owner.save(update_fields=["password"])

            Employee.objects.update_or_create(
                user=owner,
                defaults={"company": company},
            )

            for feature_code in company_seed["enabled_features"]:
                feature, _ = Feature.objects.get_or_create(
                    code=feature_code,
                    defaults={"name": feature_code.replace("_", " ").title(), "is_active": True},
                )
                CompanyFeature.objects.update_or_create(
                    company=company,
                    feature=feature,
                    defaults={"enabled": True, "granted_by": owner},
                )

            owner.user_permissions.add(
                add_employee_permission,
                manage_features_permission,
                *warehouse_permissions,
            )

            item_type_map: dict[str, ItemType] = {}
            for item_type_name in company_seed["item_types"]:
                item_type, _ = ItemType.objects.get_or_create(
                    company=company,
                    name=item_type_name,
                )
                item_type_map[item_type_name] = item_type

            manufacturer_map: dict[str, Manufacturer] = {}
            for manufacturer_name in company_seed["manufacturers"]:
                manufacturer, _ = Manufacturer.objects.get_or_create(
                    company=company,
                    name=manufacturer_name,
                )
                manufacturer_map[manufacturer_name] = manufacturer

            for item_seed in company_seed["items"]:
                Item.objects.update_or_create(
                    company=company,
                    name=item_seed["name"],
                    model=item_seed["model"],
                    defaults={
                        "type": item_type_map[item_seed["type_name"]],
                        "manufacturer": manufacturer_map[item_seed["manufacturer_name"]],
                        "quantity": item_seed["quantity"],
                        "market_value": Decimal(item_seed["market_value"]),
                        "description": item_seed["description"],
                    },
                )

        self.stdout.write(self.style.SUCCESS(
            "Base data populated successfully."))

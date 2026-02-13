from django.test import TestCase
from django.contrib.auth.models import Permission, User
from django.urls import reverse
from companies.models import Company, Employee
from .models import Item, ItemType, Manufacturer


class WarehouseTenantTests(TestCase):
    def setUp(self) -> None:
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")

        self.user = User.objects.create_user(
            username="employee-a",
            password="strong-password-123",
        )
        Employee.objects.create(user=self.user, company=self.company_a)

        self.user.user_permissions.add(
            Permission.objects.get(codename="view_item"),
            Permission.objects.get(codename="add_item"),
        )
        self.client.login(username="employee-a", password="strong-password-123")

        self.type_a = ItemType.objects.create(name="PLC", company=self.company_a)
        self.type_b = ItemType.objects.create(name="PLC", company=self.company_b)

        self.manufacturer_a = Manufacturer.objects.create(
            name="Maker A", company=self.company_a
        )
        self.manufacturer_b = Manufacturer.objects.create(
            name="Maker B", company=self.company_b
        )

        Item.objects.create(
            company=self.company_a,
            name="Visible Item",
            type=self.type_a,
            manufacturer=self.manufacturer_a,
            model="A-100",
            quantity=5,
            market_value="100.00",
        )
        Item.objects.create(
            company=self.company_b,
            name="Hidden Item",
            type=self.type_b,
            manufacturer=self.manufacturer_b,
            model="B-200",
            quantity=7,
            market_value="200.00",
        )

    def test_items_view_only_returns_company_items(self) -> None:
        response = self.client.get(reverse("warehouse:items"))

        self.assertEqual(response.status_code, 200)
        items = list(response.context["items"])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "Visible Item")

    def test_create_item_form_is_scoped_and_assigns_company(self) -> None:
        get_response = self.client.get(reverse("warehouse:create_item"))
        form = get_response.context["form"]

        self.assertQuerySetEqual(
            form.fields["type"].queryset.order_by("id"),
            ItemType.objects.filter(company=self.company_a).order_by("id"),
            transform=lambda x: x,
        )
        self.assertQuerySetEqual(
            form.fields["manufacturer"].queryset.order_by("id"),
            Manufacturer.objects.filter(company=self.company_a).order_by("id"),
            transform=lambda x: x,
        )

        post_response = self.client.post(
            reverse("warehouse:create_item"),
            data={
                "name": "Created Item",
                "type": self.type_a.id,
                "manufacturer": self.manufacturer_a.id,
                "model": "A-300",
                "quantity": 2,
                "market_value": "321.00",
                "description": "Tenant-safe item",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        created_item = Item.objects.get(name="Created Item")
        self.assertEqual(created_item.company, self.company_a)

    def test_items_view_requires_view_permission(self) -> None:
        self.user.user_permissions.remove(
            Permission.objects.get(codename="view_item"),
        )
        response = self.client.get(reverse("warehouse:items"))
        self.assertEqual(response.status_code, 403)

    def test_create_item_requires_add_permission(self) -> None:
        self.user.user_permissions.remove(
            Permission.objects.get(codename="add_item"),
        )
        response = self.client.get(reverse("warehouse:create_item"))
        self.assertEqual(response.status_code, 403)

    def test_update_item_requires_change_permission(self) -> None:
        item = Item.objects.get(name="Visible Item")
        response = self.client.post(
            reverse("warehouse:items"),
            data={
                "action": "update_item",
                "item_id": item.id,
                f"edit-{item.id}-name": "Visible Item Updated",
                f"edit-{item.id}-type": self.type_a.id,
                f"edit-{item.id}-manufacturer": self.manufacturer_a.id,
                f"edit-{item.id}-model": "A-100",
                f"edit-{item.id}-quantity": 5,
                f"edit-{item.id}-market_value": "100.00",
                f"edit-{item.id}-description": "",
            },
        )
        self.assertEqual(response.status_code, 403)
        item.refresh_from_db()
        self.assertEqual(item.name, "Visible Item")

    def test_update_item_with_change_permission(self) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(codename="change_item"),
        )
        item = Item.objects.get(name="Visible Item")
        response = self.client.post(
            reverse("warehouse:items"),
            data={
                "action": "update_item",
                "item_id": item.id,
                f"edit-{item.id}-name": "Visible Item Updated",
                f"edit-{item.id}-type": self.type_a.id,
                f"edit-{item.id}-manufacturer": self.manufacturer_a.id,
                f"edit-{item.id}-model": "A-101",
                f"edit-{item.id}-quantity": 10,
                f"edit-{item.id}-market_value": "150.00",
                f"edit-{item.id}-description": "Updated",
            },
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.name, "Visible Item Updated")
        self.assertEqual(item.quantity, 10)
        self.assertEqual(str(item.market_value), "150.00")

    def test_delete_item_requires_delete_permission(self) -> None:
        item = Item.objects.get(name="Visible Item")
        response = self.client.post(
            reverse("warehouse:items"),
            data={"action": "delete_item", "item_id": item.id},
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Item.objects.filter(pk=item.id).exists())

    def test_delete_item_with_delete_permission(self) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(codename="delete_item"),
        )
        item = Item.objects.get(name="Visible Item")
        response = self.client.post(
            reverse("warehouse:items"),
            data={"action": "delete_item", "item_id": item.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Item.objects.filter(pk=item.id).exists())

    def test_update_item_ignores_other_company_item(self) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(codename="change_item"),
        )
        other_company_item = Item.objects.get(name="Hidden Item")
        response = self.client.post(
            reverse("warehouse:items"),
            data={
                "action": "update_item",
                "item_id": other_company_item.id,
                f"edit-{other_company_item.id}-name": "Should Not Update",
                f"edit-{other_company_item.id}-type": self.type_b.id,
                f"edit-{other_company_item.id}-manufacturer": self.manufacturer_b.id,
                f"edit-{other_company_item.id}-model": "B-201",
                f"edit-{other_company_item.id}-quantity": 1,
                f"edit-{other_company_item.id}-market_value": "1.00",
                f"edit-{other_company_item.id}-description": "Nope",
            },
        )
        self.assertEqual(response.status_code, 302)
        other_company_item.refresh_from_db()
        self.assertEqual(other_company_item.name, "Hidden Item")

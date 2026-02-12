from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from users.models import Employee
from .models import Company


class CompanySignupTests(TestCase):
    def test_signup_creates_company_owner_and_employee_profile(self) -> None:
        response = self.client.post(
            reverse("companies:signup"),
            data={
                "company_name": "Acme Controls",
                "cnpj": "12345678000199",
                "first_name": "Ana",
                "last_name": "Souza",
                "username": "ana",
                "email": "ana@acme.com",
                "password": "StrongPass1",
                "password2": "StrongPass1",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("warehouse:home"))
        company = Company.objects.get(name="Acme Controls")
        self.assertEqual(company.cnpj, "12345678000199")
        user = User.objects.get(username="ana")
        employee = Employee.objects.get(user=user)
        self.assertEqual(employee.company, company)

        warehouse_permission_count = Permission.objects.filter(
            content_type__app_label="warehouse"
        ).count()
        self.assertEqual(user.user_permissions.count(), warehouse_permission_count)

        items_response = self.client.get(reverse("warehouse:items"))
        self.assertEqual(items_response.status_code, 200)

    def test_duplicate_cnpj_is_rejected(self) -> None:
        Company.objects.create(name="Acme Controls", cnpj="12345678000199")

        response = self.client.post(
            reverse("companies:signup"),
            data={
                "company_name": "Another Name",
                "cnpj": "12.345.678/0001-99",
                "first_name": "Ana",
                "last_name": "Souza",
                "username": "ana2",
                "email": "ana2@acme.com",
                "password": "StrongPass1",
                "password2": "StrongPass1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from .forms import EmployeeRegisterForm
from .models import Company, Employee


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
        self.assertEqual(user.user_permissions.count(), warehouse_permission_count + 1)
        self.assertTrue(user.has_perm("companies.add_employee"))

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


class EmployeeRegisterFormTests(TestCase):
    def test_save_creates_employee_association(self) -> None:
        company = Company.objects.create(name="Tenant Co")

        form = EmployeeRegisterForm(
            data={
                "first_name": "Maria",
                "last_name": "Silva",
                "username": "maria",
                "email": "maria@example.com",
                "password": "StrongPassword1",
                "password2": "StrongPassword1",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        user = form.save(company=company)
        employee = Employee.objects.get(user=user)
        self.assertEqual(employee.company, company)


class EmployeeRegisterViewTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(name="Tenant Co", cnpj="12345678000199")
        self.admin_user = User.objects.create_user(
            username="tenant-admin",
            password="StrongPassword1",
        )
        Employee.objects.create(user=self.admin_user, company=self.company)
        self.admin_user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="companies",
                codename="add_employee",
            )
        )

    def test_anonymous_user_cannot_access_register_view(self) -> None:
        response = self.client.get(reverse("companies:register_employee"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("companies:login"), response.url)

    def test_company_admin_registers_employee_for_own_company(self) -> None:
        self.client.login(username="tenant-admin", password="StrongPassword1")
        response = self.client.post(
            reverse("companies:register_employee"),
            data={
                "first_name": "Joao",
                "last_name": "Silva",
                "username": "joao",
                "email": "joao@example.com",
                "password": "StrongPassword1",
                "password2": "StrongPassword1",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("companies:register_employee"))
        created_user = User.objects.get(username="joao")
        employee = Employee.objects.get(user=created_user)
        self.assertEqual(employee.company, self.company)

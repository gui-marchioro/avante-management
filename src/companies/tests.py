from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from .admin import CompanyFeatureAdmin
from .forms import EmployeeRegisterForm
from .models import Company, CompanyFeature, Employee, Feature


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
        self.assertEqual(response.url, reverse("companies:home"))

        company = Company.objects.get(name="Acme Controls")
        self.assertEqual(company.cnpj, "12345678000199")
        user = User.objects.get(username="ana")
        employee = Employee.objects.get(user=user)
        self.assertEqual(employee.company, company)

        warehouse_permission_count = Permission.objects.filter(
            content_type__app_label="warehouse"
        ).count()
        self.assertEqual(user.user_permissions.count(),
                         warehouse_permission_count + 1)
        self.assertTrue(user.has_perm("companies.add_employee"))
        self.assertTrue(user.has_perm("companies.manage_company_features"))
        self.assertTrue(company.has_feature("companies"))

        home_response = self.client.get(reverse("companies:home"))
        self.assertEqual(home_response.status_code, 200)

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


class CompanyFeatureTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(
            name="Feature Co", cnpj="11111111000111")
        self.feature = Feature.objects.create(
            code="warehouse",
            name="Warehouse",
            is_active=True,
        )

    def test_company_has_feature_only_when_enabled(self) -> None:
        self.assertFalse(self.company.has_feature("warehouse"))
        CompanyFeature.objects.create(
            company=self.company,
            feature=self.feature,
            enabled=True,
        )
        self.assertTrue(self.company.has_feature("warehouse"))

    def test_company_feature_admin_is_superuser_only_for_changes(self) -> None:
        site = AdminSite()
        model_admin = CompanyFeatureAdmin(CompanyFeature, site)
        factory = RequestFactory()

        superuser = User.objects.create_superuser(
            username="root",
            email="root@example.com",
            password="StrongPassword1",
        )
        staff = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="StrongPassword1",
            is_staff=True,
        )

        super_request = factory.get("/admin/companies/companyfeature/")
        super_request.user = superuser
        self.assertTrue(model_admin.has_add_permission(super_request))
        self.assertTrue(model_admin.has_change_permission(super_request))
        self.assertTrue(model_admin.has_delete_permission(super_request))

        staff_request = factory.get("/admin/companies/companyfeature/")
        staff_request.user = staff
        self.assertFalse(model_admin.has_add_permission(staff_request))
        self.assertFalse(model_admin.has_change_permission(staff_request))
        self.assertFalse(model_admin.has_delete_permission(staff_request))

    def test_feature_code_must_match_app_label(self) -> None:
        valid_feature = Feature(code="auth", name="Auth")
        valid_feature.full_clean()

        invalid_feature = Feature(code="nonexistent_app", name="Invalid")
        with self.assertRaises(ValidationError):
            invalid_feature.full_clean()


class CompanyFeatureToggleViewTests(TestCase):
    def setUp(self) -> None:
        self.company_a = Company.objects.create(
            name="Tenant A", cnpj="22222222000122")
        self.company_b = Company.objects.create(
            name="Tenant B", cnpj="33333333000133")

        self.superuser = User.objects.create_superuser(
            username="root-admin",
            email="root@example.com",
            password="StrongPassword1",
        )
        Employee.objects.create(user=self.superuser, company=self.company_a)
        self.regular_user = User.objects.create_user(
            username="tenant-admin",
            password="StrongPassword1",
        )
        Employee.objects.create(user=self.regular_user, company=self.company_a)

        feature_warehouse = Feature.objects.create(
            code="warehouse", name="Warehouse")
        feature_auth, _ = Feature.objects.get_or_create(
            code="auth",
            defaults={"name": "Auth"},
        )

        self.grant_a = CompanyFeature.objects.create(
            company=self.company_a, feature=feature_warehouse, enabled=True
        )
        self.grant_b = CompanyFeature.objects.create(
            company=self.company_b, feature=feature_auth, enabled=True
        )

    def test_superuser_can_toggle_only_own_company_grants(self) -> None:
        self.client.login(username="root-admin", password="StrongPassword1")
        response = self.client.post(
            reverse("companies:company_features"),
            data={},
        )
        self.assertEqual(response.status_code, 302)

        self.grant_a.refresh_from_db()
        self.grant_b.refresh_from_db()
        self.assertFalse(self.grant_a.enabled)
        self.assertTrue(self.grant_b.enabled)

    def test_anonymous_user_is_redirected_from_feature_toggle_view(self) -> None:
        response = self.client.get(reverse("companies:company_features"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("companies:login"), response.url)

    def test_non_superuser_cannot_access_feature_toggle_view(self) -> None:
        self.client.login(username="tenant-admin", password="StrongPassword1")
        response = self.client.get(reverse("companies:company_features"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("companies:login"), response.url)


class CompanyHomeViewTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(
            name="Home Co", cnpj="44444444000144")
        self.user = User.objects.create_user(
            username="home-admin",
            first_name="Helena",
            password="StrongPassword1",
        )
        Employee.objects.create(user=self.user, company=self.company)
        self.client.login(username="home-admin", password="StrongPassword1")

        warehouse_feature, _ = Feature.objects.get_or_create(
            code="warehouse",
            defaults={"name": "Warehouse"},
        )
        CompanyFeature.objects.update_or_create(
            company=self.company,
            feature=warehouse_feature,
            defaults={"enabled": True},
        )

        self.employee_user = User.objects.create_user(
            username="operator-1",
            first_name="Carlos",
            last_name="Silva",
            email="carlos@example.com",
            password="StrongPassword1",
        )
        Employee.objects.create(user=self.employee_user, company=self.company)

    def test_homepage_shows_company_info(self) -> None:
        response = self.client.get(reverse("companies:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Helena")
        self.assertContains(response, "Home Co")
        self.assertContains(response, "44444444000144")

    def test_homepage_shows_company_employee_list(self) -> None:
        response = self.client.get(reverse("companies:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Funcionários cadastrados")
        self.assertContains(response, reverse("companies:employees"))
        self.assertContains(response, "home-admin")
        self.assertContains(response, "operator-1")
        self.assertContains(response, "Carlos")

    def test_homepage_has_enabled_and_disabled_feature_buttons(self) -> None:
        auth_feature, _ = Feature.objects.get_or_create(
            code="auth",
            defaults={"name": "Auth"},
        )
        CompanyFeature.objects.filter(
            company=self.company, feature=auth_feature).delete()

        response = self.client.get(reverse("companies:home"))
        self.assertContains(response, reverse("warehouse:home"))
        self.assertContains(response, "auth (not granted)")

    def test_sidebar_lists_only_enabled_features(self) -> None:
        warehouse_feature = Feature.objects.get(code="warehouse")
        CompanyFeature.objects.filter(
            company=self.company,
            feature=warehouse_feature,
        ).update(enabled=False)

        response = self.client.get(reverse("companies:home"))
        self.assertContains(response, "Companies")
        self.assertNotContains(response, reverse("warehouse:home"))


class CompanyEmployeesViewTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(
            name="Employees Co", cnpj="66666666000166")
        self.user = User.objects.create_user(
            username="employees-admin",
            password="StrongPassword1",
        )
        Employee.objects.create(user=self.user, company=self.company)
        self.client.login(username="employees-admin", password="StrongPassword1")

        self.employee_user = User.objects.create_user(
            username="employees-operator",
            first_name="Paula",
            email="paula@example.com",
            password="StrongPassword1",
        )
        Employee.objects.create(user=self.employee_user, company=self.company)

    def test_employees_page_loads_company_employees(self) -> None:
        response = self.client.get(reverse("companies:employees"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Funcionários cadastrados")
        self.assertContains(response, "employees-admin")
        self.assertContains(response, "employees-operator")
        self.assertContains(response, "paula@example.com")

    def test_employees_page_requires_authentication(self) -> None:
        self.client.logout()
        response = self.client.get(reverse("companies:employees"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("companies:login"), response.url)

    def test_employees_page_hides_management_actions_without_permissions(self) -> None:
        response = self.client.get(reverse("companies:employees"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Adicionar funcionário")
        self.assertNotContains(response, "Salvar alterações")
        self.assertNotContains(response, "Remover funcionário")
        self.assertNotContains(response, "Salvar grupos")

    def test_add_employee_requires_permission(self) -> None:
        response = self.client.post(
            reverse("companies:employees"),
            data={
                "action": "add_employee",
                "add-first_name": "Ana",
                "add-last_name": "Silva",
                "add-username": "ana-employees",
                "add-email": "ana@example.com",
                "add-password": "StrongPassword1",
                "add-password2": "StrongPassword1",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="ana-employees").exists())

    def test_add_employee_with_permission(self) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="companies",
                codename="add_employee",
            ),
        )
        response = self.client.post(
            reverse("companies:employees"),
            data={
                "action": "add_employee",
                "add-first_name": "Ana",
                "add-last_name": "Silva",
                "add-username": "ana-employees",
                "add-email": "ana@example.com",
                "add-password": "StrongPassword1",
                "add-password2": "StrongPassword1",
            },
        )
        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(username="ana-employees")
        self.assertTrue(
            Employee.objects.filter(user=created_user, company=self.company).exists()
        )

    def test_update_employee_with_permission(self) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="companies",
                codename="change_employee",
            ),
        )
        target_employee = Employee.objects.get(user=self.employee_user)
        response = self.client.post(
            reverse("companies:employees"),
            data={
                "action": "update_employee",
                "employee_id": target_employee.id,
                f"edit-{target_employee.id}-first_name": "Paula Updated",
                f"edit-{target_employee.id}-last_name": "Operator",
                f"edit-{target_employee.id}-username": "employees-operator",
                f"edit-{target_employee.id}-email": "paula.updated@example.com",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee_user.first_name, "Paula Updated")
        self.assertEqual(self.employee_user.email, "paula.updated@example.com")

    def test_delete_employee_with_permission(self) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="companies",
                codename="delete_employee",
            ),
        )
        target_employee = Employee.objects.get(user=self.employee_user)
        response = self.client.post(
            reverse("companies:employees"),
            data={
                "action": "delete_employee",
                "employee_id": target_employee.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.employee_user.id).exists())
        self.assertFalse(Employee.objects.filter(pk=target_employee.id).exists())

    def test_update_employee_groups_with_permissions(self) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="auth",
                codename="change_user",
            ),
            Permission.objects.get(
                content_type__app_label="auth",
                codename="view_group",
            ),
        )
        target_employee = Employee.objects.get(user=self.employee_user)
        viewer_group = Group.objects.create(name="custom_viewer")

        response = self.client.post(
            reverse("companies:employees"),
            data={
                "action": "update_employee_groups",
                "employee_id": target_employee.id,
                f"groups-{target_employee.id}-groups": [viewer_group.id],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.employee_user.refresh_from_db()
        self.assertIn(viewer_group, self.employee_user.groups.all())


class CompanyConfigurationViewTests(TestCase):
    def setUp(self) -> None:
        self.company = Company.objects.create(
            name="Config Co", cnpj="55555555000155")
        self.admin_user = User.objects.create_user(
            username="config-admin",
            password="StrongPassword1",
        )
        Employee.objects.create(user=self.admin_user, company=self.company)
        self.admin_user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="companies",
                codename="add_employee",
            ),
        )
        self.client.login(username="config-admin", password="StrongPassword1")

        warehouse_feature, _ = Feature.objects.get_or_create(
            code="warehouse",
            defaults={"name": "Warehouse"},
        )
        self.grant = CompanyFeature.objects.update_or_create(
            company=self.company,
            feature=warehouse_feature,
            defaults={"enabled": True},
        )[0]

    def test_company_configuration_page_loads(self) -> None:
        response = self.client.get(reverse("companies:company_configuration"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informações da empresa")
        self.assertContains(response, "Funcionários")
        self.assertNotContains(response, "Features da empresa")

    def test_company_configuration_updates_company_and_employees(self) -> None:
        self.admin_user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="companies",
                codename="change_company",
            ),
        )
        response = self.client.post(
            reverse("companies:company_configuration"),
            data={"action": "update_company",
                  "name": "Config Co Updated", "cnpj": "55.555.555/0001-55"},
        )
        self.assertEqual(response.status_code, 302)
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, "Config Co Updated")
        self.assertEqual(self.company.cnpj, "55555555000155")

        response = self.client.post(
            reverse("companies:company_configuration"),
            data={
                "action": "add_employee",
                "add-first_name": "Julia",
                "add-last_name": "Santos",
                "add-username": "julia",
                "add-email": "julia@example.com",
                "add-password": "StrongPassword1",
                "add-password2": "StrongPassword1",
            },
        )
        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(username="julia")
        created_employee = Employee.objects.get(user=created_user)
        self.assertEqual(created_employee.company, self.company)

        self.admin_user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="companies",
                codename="delete_employee",
            ),
        )
        response = self.client.post(
            reverse("companies:company_configuration"),
            data={"action": "remove_employee",
                  "employee_id": created_employee.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username="julia").exists())

    def test_company_configuration_can_only_enable_features(self) -> None:
        self.grant.enabled = False
        self.grant.save(update_fields=["enabled"])

        response = self.client.post(
            reverse("companies:company_configuration"),
            data={"action": "toggle_features",
                  f"feature_{self.grant.id}": "on"},
        )
        self.assertEqual(response.status_code, 403)
        self.grant.refresh_from_db()
        self.assertFalse(self.grant.enabled)

        manage_features_permission, _ = Permission.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Company),
            codename="manage_company_features",
            defaults={"name": "Can manage company feature activation"},
        )
        self.admin_user.user_permissions.add(manage_features_permission)

        response = self.client.post(
            reverse("companies:company_configuration"),
            data={"action": "toggle_features",
                  f"feature_{self.grant.id}": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.grant.refresh_from_db()
        self.assertTrue(self.grant.enabled)

    def test_company_configuration_updates_employee_and_groups_with_permissions(self) -> None:
        target_user = User.objects.create_user(
            username="config-operator",
            first_name="Config",
            last_name="Operator",
            email="config-operator@example.com",
            password="StrongPassword1",
        )
        target_employee = Employee.objects.create(
            user=target_user, company=self.company)

        self.admin_user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="companies",
                codename="change_employee",
            ),
            Permission.objects.get(
                content_type__app_label="auth",
                codename="change_user",
            ),
            Permission.objects.get(
                content_type__app_label="auth",
                codename="view_group",
            ),
        )
        reviewer_group = Group.objects.create(name="config_reviewer")

        response = self.client.post(
            reverse("companies:company_configuration"),
            data={
                "action": "update_employee",
                "employee_id": target_employee.id,
                f"edit-{target_employee.id}-first_name": "Config Updated",
                f"edit-{target_employee.id}-last_name": "Operator",
                f"edit-{target_employee.id}-username": "config-operator",
                f"edit-{target_employee.id}-email": "config-updated@example.com",
            },
        )
        self.assertEqual(response.status_code, 302)
        target_user.refresh_from_db()
        self.assertEqual(target_user.first_name, "Config Updated")
        self.assertEqual(target_user.email, "config-updated@example.com")

        response = self.client.post(
            reverse("companies:company_configuration"),
            data={
                "action": "update_employee_groups",
                "employee_id": target_employee.id,
                f"groups-{target_employee.id}-groups": [reviewer_group.id],
            },
        )
        self.assertEqual(response.status_code, 302)
        target_user.refresh_from_db()
        self.assertIn(reviewer_group, target_user.groups.all())


class StandardGroupsTests(TestCase):
    def test_warehouse_groups_have_expected_permissions(self) -> None:
        warehouse_viewer = Group.objects.get(name="warehouse_viewer")
        warehouse_editor = Group.objects.get(name="warehouse_editor")
        warehouse_admin = Group.objects.get(name="warehouse_admin")

        self.assertTrue(
            warehouse_viewer.permissions.filter(
                content_type__app_label="warehouse",
                codename="view_item",
            ).exists()
        )
        self.assertFalse(
            warehouse_viewer.permissions.filter(
                content_type__app_label="warehouse",
                codename="add_item",
            ).exists()
        )
        self.assertTrue(
            warehouse_editor.permissions.filter(
                content_type__app_label="warehouse",
                codename="change_item",
            ).exists()
        )
        self.assertFalse(
            warehouse_editor.permissions.filter(
                content_type__app_label="warehouse",
                codename="view_financial_dashboard",
            ).exists()
        )
        self.assertTrue(
            warehouse_admin.permissions.filter(
                content_type__app_label="warehouse",
                codename="view_financial_dashboard",
            ).exists()
        )

    def test_company_groups_have_expected_permissions(self) -> None:
        company_viewer = Group.objects.get(name="company_viewer")
        company_editor = Group.objects.get(name="company_editor")
        company_admin = Group.objects.get(name="company_admin")

        self.assertTrue(
            company_viewer.permissions.filter(
                content_type__app_label="companies",
                codename="view_company",
            ).exists()
        )
        self.assertFalse(
            company_viewer.permissions.filter(
                content_type__app_label="companies",
                codename="change_company",
            ).exists()
        )
        self.assertTrue(
            company_editor.permissions.filter(
                content_type__app_label="companies",
                codename="change_company",
            ).exists()
        )
        self.assertFalse(
            company_admin.permissions.filter(
                content_type__app_label="companies",
                codename="manage_company_features",
            ).exists()
        )
        self.assertTrue(
            company_admin.permissions.filter(
                content_type__app_label="auth",
                codename="change_user",
            ).exists()
        )

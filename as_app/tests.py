import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from as_app.models import ASTicket, Brand, Company, CompanyCategory, Tool


class MultiSelectAdminFilterTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="admin_test",
            email="admin_test@example.com",
            password="password123",
        )
        self.client.force_login(self.admin_user)

        price_group = CompanyCategory.objects.create(name="A")
        self.company_a = Company.objects.create(
            name="다스",
            estimate_company_name="다스",
            business_number="123-45-67890",
            representative="홍길동",
            address="충남 아산시",
            price_group=price_group,
        )
        self.company_b = Company.objects.create(
            name="대원정밀",
            estimate_company_name="대원정밀",
            business_number="987-65-43210",
            representative="김철수",
            address="경기 안산시",
            price_group=price_group,
        )
        self.brand = Brand.objects.create(name="GESIPA")
        self.tool = Tool.objects.create(brand=self.brand, model_name="TAURUS2")

        self.shipped_ticket = ASTicket.objects.create(
            inbound_date=datetime.date(2026, 4, 12),
            outbound_date=datetime.date(2026, 4, 20),
            company=self.company_a,
            manager="담당자A",
            tool=self.tool,
            serial_number="SN-SHIPPED",
            symptom="출고 대상",
            repair_content="수리 완료",
            status=ASTicket.Status.SHIPPED,
            repair_cost=1000,
        )
        self.estimate_ticket = ASTicket.objects.create(
            inbound_date=datetime.date(2026, 4, 10),
            company=self.company_b,
            manager="담당자B",
            tool=self.tool,
            serial_number="SN-ESTIMATE",
            symptom="견적 대상",
            repair_content="견적 진행",
            status=ASTicket.Status.ESTIMATE_DONE,
            repair_cost=2000,
        )
        self.repaired_ticket = ASTicket.objects.create(
            inbound_date=datetime.date(2026, 4, 11),
            company=self.company_a,
            manager="담당자C",
            tool=self.tool,
            serial_number="SN-REPAIRED",
            symptom="상태 등록 대상",
            repair_content="수리 완료 대기",
            status=ASTicket.Status.REPAIRED,
            repair_cost=3000,
        )

    def assert_admin_filter_count(self, url_name, params, expected_count):
        response = self.client.get(reverse(url_name), params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cl"].result_count, expected_count)
        self.assertNotIn("e=1", response.request.get("QUERY_STRING", ""))

    def test_ashistory_filters_allow_custom_query_params(self):
        self.assert_admin_filter_count(
            "admin:as_app_ashistory_changelist",
            {"mf_status": ASTicket.Status.SHIPPED},
            1,
        )
        self.assert_admin_filter_count(
            "admin:as_app_ashistory_changelist",
            {
                "mf_inbound_date_from": "2026-04-10",
                "mf_inbound_date_to": "2026-04-11",
            },
            2,
        )
        self.assert_admin_filter_count(
            "admin:as_app_ashistory_changelist",
            {
                "mf_outbound_date_from": "2026-04-20",
                "mf_outbound_date_to": "2026-04-20",
            },
            1,
        )

    def test_estimate_ticket_filters_allow_custom_query_params(self):
        self.assert_admin_filter_count(
            "admin:as_app_estimateticket_changelist",
            {"mf_status": ASTicket.Status.ESTIMATE_DONE},
            1,
        )

    def test_tax_invoice_filters_allow_custom_query_params(self):
        self.assert_admin_filter_count(
            "admin:as_app_taxinvoiceticket_changelist",
            {
                "mf_outbound_date_from": "2026-04-20",
                "mf_outbound_date_to": "2026-04-20",
            },
            1,
        )

    def test_status_registration_filters_allow_custom_query_params(self):
        self.assert_admin_filter_count(
            "admin:as_app_statusregistration_changelist",
            {"mf_status": ASTicket.Status.REPAIRED},
            1,
        )
        self.assert_admin_filter_count(
            "admin:as_app_statusregistration_changelist",
            {
                "mf_inbound_date_from": "2026-04-11",
                "mf_inbound_date_to": "2026-04-11",
            },
            1,
        )

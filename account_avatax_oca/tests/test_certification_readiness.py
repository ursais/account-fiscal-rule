# Copyright 2026 Open Source Integrators
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unittest.mock import patch

from odoo.tests import common

from ..models import avatax_rest_api
from ..models.avatax_rest_api import AvaTaxRESTService


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class FakeAddress:
    def __init__(self, street, city, state, zip_code):
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code

    def get_avatax_address(self):
        return {
            "line1": self.street,
            "city": self.city,
            "region": self.state,
            "postalCode": self.zip_code,
            "country": "US",
        }


class FakeLineRef:
    def __init__(self, line_id):
        self.id = line_id


class FakeAvataxClientCapture:
    def __init__(self, app_name, app_version, machine_name, environment):
        self.app_name = app_name
        self.app_version = app_version
        self.machine_name = machine_name
        self.environment = environment
        self.client_id = ""
        self.client_header = {}
        self.credentials = None
        self.last_payload = None

    def add_credentials(self, username, password):
        self.credentials = (username, password)

    def create_or_adjust_transaction(self, payload):
        self.last_payload = payload
        return FakeResponse(
            {
                "lines": [
                    {
                        "details": [
                            {
                                "rate": 0.0825,
                                "tax": 1.65,
                            }
                        ]
                    }
                ]
            }
        )


class TestCertificationReadiness(common.TransactionCase):
    def _build_service(self):
        with patch.object(avatax_rest_api, "AvataxClient", FakeAvataxClientCapture):
            return AvaTaxRESTService(
                username="account",
                password="license",
                url="https://sandbox-rest.avatax.com/api/v2",
            )

    def test_certified_header_value_is_forced(self):
        service = self._build_service()
        self.assertEqual(
            service.client.client_id,
            AvaTaxRESTService.AVALARA_CLIENT_HEADER,
        )
        self.assertEqual(
            service.client.client_header.get("X-Avalara-Client"),
            AvaTaxRESTService.AVALARA_CLIENT_HEADER,
        )

    def test_payload_supports_multiline_shipping_and_location(self):
        service = self._build_service()
        origin = FakeAddress("100 Origin St", "Austin", "TX", "73301")
        destination = FakeAddress("200 Ship St", "Phoenix", "AZ", "85001")
        lines = [
            {
                "id": FakeLineRef(1),
                "description": "Primary Product",
                "itemcode": "ITEM-001",
                "qty": 2,
                "amount": 25.0,
                "tax_code": "PC030000",
            },
            {
                "id": FakeLineRef(2),
                "description": "Shipping",
                "itemcode": "SHIP-001",
                "qty": 1,
                "amount": 10.0,
                "tax_code": "FR000000",
            },
        ]

        service.get_tax(
            company_code="COMPANY-A",
            doc_date="2026-03-06",
            doc_type="SalesInvoice",
            partner_code="CUSTOMER-123",
            doc_code="INV-0001",
            origin=origin,
            destination=destination,
            received_lines=lines,
            reference_code="SO-0001",
            location_code="WH-A",
            currency_code="USD",
            vat="US123456",
        )

        payload = service.client.last_payload["createTransactionModel"]
        self.assertEqual(payload["code"], "INV-0001")
        self.assertEqual(payload["customerCode"], "CUSTOMER-123")
        self.assertEqual(payload["reportingLocationCode"], "WH-A")
        self.assertEqual(len(payload["lines"]), 2)
        self.assertEqual(payload["lines"][1]["taxCode"], "FR000000")
        self.assertEqual(payload["lines"][1]["amount"], 10.0)

    def test_payload_supports_exemption_usage_and_return_override(self):
        service = self._build_service()
        origin = FakeAddress("100 Origin St", "Austin", "TX", "73301")
        destination = FakeAddress("200 Ship St", "Phoenix", "AZ", "85001")
        lines = [
            {
                "id": FakeLineRef(1),
                "description": "Return Item",
                "itemcode": "ITEM-RETURN-1",
                "qty": 1,
                "amount": -15.0,
                "tax_code": "PC030000",
            }
        ]

        service.get_tax(
            company_code="COMPANY-A",
            doc_date="2026-03-06",
            doc_type="ReturnInvoice",
            partner_code="CUSTOMER-123",
            doc_code="RINV-0001",
            origin=origin,
            destination=destination,
            received_lines=lines,
            exemption_no="EXEMPT-100",
            customer_usage_type="A",
            is_override=True,
            invoice_date="2026-03-06",
        )

        payload = service.client.last_payload["createTransactionModel"]
        self.assertEqual(payload["entityUseCode"], "A")
        self.assertEqual(payload["exemptionNo"], "EXEMPT-100")
        self.assertEqual(payload["lines"][0]["amount"], -15.0)
        self.assertEqual(payload["taxOverride"]["type"], "TaxDate")

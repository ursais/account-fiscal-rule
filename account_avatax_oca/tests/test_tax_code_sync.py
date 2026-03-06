# Copyright 2026 Open Source Integrators
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unittest.mock import patch

from odoo.tests import common

from ..models import avalara_salestax


class FakeAvaTaxService:
    def __init__(self, config=None):
        self.config = config

    def list_tax_codes(self):
        return [
            {
                "taxCode": "P0000000",
                "description": "Tangible personal property",
                "taxCodeType": "Product",
            },
            {
                "taxCode": "FR020100",
                "description": "Freight",
                "taxCodeType": "Freight",
            },
            {
                "code": "SVC00000",
                "name": "Service labor",
            },
        ]


class TestTaxCodeSync(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env["avalara.salestax"].create(
            {
                "account_number": "SYNC-TEST-ACCOUNT",
                "license_key": "SYNC-TEST-LICENSE",
                "company_code": "SYNC-TEST-COMPANY",
                "company_id": cls.env.company.id,
                "service_url": "https://sandbox-rest.avatax.com/api/v2",
            }
        )

    def test_action_sync_tax_codes_creates_and_updates_codes(self):
        existing = self.env["product.tax.code"].create(
            {
                "name": "P0000000",
                "description": "Old description",
                "type": "other",
            }
        )
        with patch.object(avalara_salestax, "AvaTaxRESTService", FakeAvaTaxService):
            action = self.config.action_sync_tax_codes()

        self.assertEqual(action.get("tag"), "display_notification")
        self.assertEqual(action.get("type"), "ir.actions.client")

        existing.invalidate_recordset(["description", "type"])
        self.assertEqual(existing.description, "Tangible personal property")
        self.assertEqual(existing.type, "product")

        freight = self.env["product.tax.code"].search(
            [("name", "=", "FR020100")], limit=1
        )
        self.assertTrue(freight)
        self.assertEqual(freight.type, "freight")

        service = self.env["product.tax.code"].search(
            [("name", "=", "SVC00000")], limit=1
        )
        self.assertTrue(service)
        self.assertEqual(service.type, "service")
        self.assertTrue(self.config.tax_code_last_sync)

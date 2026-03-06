# Copyright 2022 Open Source Integrators
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


class FakeAvataxClientBase:
    def __init__(self, app_name, app_version, machine_name, environment):
        self.app_name = app_name
        self.app_version = app_version
        self.machine_name = machine_name
        self.environment = environment
        self.client_id = ""
        self.client_header = {}
        self.credentials = None

    def add_credentials(self, username, password):
        self.credentials = (username, password)


class FakeAvataxClientWithList(FakeAvataxClientBase):
    def list_tax_codes(self):
        return FakeResponse({"value": [{"taxCode": "P0000000"}]})


class FakeAvataxClientWithQuery(FakeAvataxClientBase):
    def query_tax_codes(self):
        return FakeResponse({"value": [{"taxCode": "D0000000"}]})


class TestAvatax(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.API = AvaTaxRESTService()

    def test_enrich_result_lines_with_tax_rate(self):
        avatax_result = {
            "lines": [
                {
                    "details": [
                        {
                            "rate": 0.056,
                            "tax": 0.0,
                            "taxCalculated": 0.0,
                            "taxName": "AZ STATE TAX",
                            "taxableAmount": 0.0,
                        },
                        {
                            "rate": 0.007,
                            "tax": 0.0,
                            "taxCalculated": 0.0,
                            "taxName": "AZ COUNTY TAX",
                            "taxableAmount": 0.0,
                        },
                        {
                            "rate": 0.018,
                            "tax": 0.16,
                            "taxCalculated": 0.16,
                            "taxName": "AZ CITY TAX",
                            "taxableAmount": 9.0,
                        },
                    ],
                    "isItemTaxable": True,
                    "lineAmount": 9.0,
                    "tax": 0.16,
                    "taxCalculated": 0.16,
                    "taxableAmount": 9.0,
                }
            ]
        }
        result = self.API._enrich_result_lines_with_tax_rate(avatax_result)
        rate = result["lines"][0]["rate"]
        self.assertEqual(rate, 1.8)

    def test_certified_client_header(self):
        with patch.object(
            avatax_rest_api, "AvataxClient", FakeAvataxClientWithList
        ):
            api = AvaTaxRESTService(
                username="account",
                password="license",
                url="https://sandbox-rest.avatax.com/api/v2",
            )
        self.assertEqual(
            api.client.client_id,
            AvaTaxRESTService.AVALARA_CLIENT_HEADER,
        )
        self.assertEqual(
            api.client.client_header.get("X-Avalara-Client"),
            AvaTaxRESTService.AVALARA_CLIENT_HEADER,
        )

    def test_list_tax_codes_uses_list_endpoint(self):
        with patch.object(
            avatax_rest_api, "AvataxClient", FakeAvataxClientWithList
        ):
            api = AvaTaxRESTService(
                username="account",
                password="license",
                url="https://sandbox-rest.avatax.com/api/v2",
            )
        tax_codes = api.list_tax_codes()
        self.assertEqual(tax_codes, [{"taxCode": "P0000000"}])

    def test_list_tax_codes_falls_back_to_query_endpoint(self):
        with patch.object(
            avatax_rest_api, "AvataxClient", FakeAvataxClientWithQuery
        ):
            api = AvaTaxRESTService(
                username="account",
                password="license",
                url="https://sandbox-rest.avatax.com/api/v2",
            )
        tax_codes = api.list_tax_codes()
        self.assertEqual(tax_codes, [{"taxCode": "D0000000"}])

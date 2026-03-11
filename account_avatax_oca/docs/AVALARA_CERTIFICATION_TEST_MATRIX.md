# Avalara Certification Test Matrix (Working Draft)

## Purpose
This matrix is a working draft based on Avalara public certification guidance and
the certify endpoint behavior. It will be reconciled against your official
certification packet once shared.

## Scope
- Module under certification work: `account_avatax_oca`
- Related extension in this stack: `mit_avatax_extended`
- Explicitly excluded: core Odoo/Enterprise AvaTax modules

## Matrix
| Test Case / Check | Requirement Type | Implementation / Control | Automated Test | Manual Evidence |
| --- | --- | --- | --- | --- |
| `X-Avalara-Client` must be `Odoo;a0nUz00000lVIX3IAO` | Mandatory | REST client header is forced in `AvaTaxRESTService` | `tests/test_rest_api.py::test_certified_client_header`, `tests/test_certification_readiness.py::test_certified_header_value_is_forced` | Run test transaction and confirm request header in Avalara logs |
| AvaTax tax code retrieval from Avalara definitions | Recommended | `list_tax_codes` + `action_sync_tax_codes` upsert `product.tax.code` | `tests/test_rest_api.py` list endpoint tests, `tests/test_tax_code_sync.py` | Click **Sync Tax Codes** and verify created/updated tax codes |
| Multi-line transaction support | Mandatory behavior (public badge guidance) | `get_tax` sends all line items to Avalara | `tests/test_certification_readiness.py::test_payload_supports_multiline_shipping_and_location` | Validate tax result on order/invoice with multiple lines |
| Shipping line handling | Mandatory behavior | Shipping line tax code is sent as a regular line | `tests/test_certification_readiness.py::test_payload_supports_multiline_shipping_and_location` | Validate freight tax behavior in transaction detail |
| Location code propagation | Mandatory behavior for multi-location installs | `reportingLocationCode` is mapped from Odoo | `tests/test_certification_readiness.py::test_payload_supports_multiline_shipping_and_location` | Create transaction from non-default location and inspect request |
| Exemption + entity use code support | Mandatory behavior | `exemptionNo` and `entityUseCode` mapped in request | `tests/test_certification_readiness.py::test_payload_supports_exemption_usage_and_return_override` | Run exempt transaction and confirm no `NoExemptionNoOrCustomerUsageType` warning |
| Negative return / override support | Mandatory behavior | Negative line amounts and `taxOverride` are supported | `tests/test_certification_readiness.py::test_payload_supports_exemption_usage_and_return_override` | Create return/credit flow and verify payload in Avalara |

## Certify Endpoint Readiness (Public Signals)
The Avalara certify endpoint evaluates transaction diversity over recent docs.
The following checks should be covered in UAT data generation before submission:

1. Do not use only generic tax code `P0000000`.
2. Use real customer and document codes (not GUID placeholders).
3. Ensure at least 2 committed invoices are present.
4. Ensure at least one void/cancel event exists.
5. Include at least one multi-line transaction.
6. Include at least one shipping line.
7. Include transaction variety: exemption, usage type, negative return, and multiple addresses.
8. Use `locationCode` where applicable.

## Finalization Step
When official test cases are provided, convert each row to:
- `TC-ID`
- Preconditions
- Exact Odoo steps
- Expected AvaTax request/response assertions
- Pass/fail evidence artifact path

# Avalara Certification Validation

## Implemented Changes

### 1) Mandatory Header Update
- File: `models/avatax_rest_api.py`
- Implemented constant:
  - `AvaTaxRESTService.AVALARA_CLIENT_HEADER = "Odoo;a0nUz00000lVIX3IAO"`
- Service now explicitly applies this value to SDK runtime fields so requests carry the certified identifier.

### 2) Dynamic Tax Code Retrieval
- Files:
  - `models/avatax_rest_api.py`
  - `models/avalara_salestax.py`
  - `views/avalara_salestax_view.xml`
- Added:
  - SDK tax-code list method (`list_tax_codes`)
  - Config action `action_sync_tax_codes` to sync Avalara tax codes into `product.tax.code`
  - UI button **Sync Tax Codes** and `Last Tax Code Sync` timestamp on AvaTax configuration

## Automated Coverage
- `tests/test_rest_api.py`
  - Enforces certified header value assignment.
  - Verifies tax-code listing endpoint behavior and fallback.
- `tests/test_tax_code_sync.py`
  - Verifies sync action updates existing codes and creates new records.
  - Verifies sync timestamp update.
- `tests/test_certification_readiness.py`
  - Verifies request payload includes key certification fields and diversity signals
    (multi-line, shipping, location, exemption/entity use, return override).

## Working Test Matrix
- See `docs/AVALARA_CERTIFICATION_TEST_MATRIX.md` for the draft matrix used until
  official certification test cases are provided.

## Manual Validation Checklist
1. Open `Accounting > Configuration > AvaTax > AvaTax API`.
2. Open active AvaTax config and click **Sync Tax Codes**.
3. Confirm success notification and `Last Tax Code Sync` value.
4. Open `Accounting > Configuration > AvaTax > Product Tax Codes` and verify new/updated codes.
5. Execute a test taxable transaction and confirm Avalara sees:
   - `X-Avalara-Client: Odoo;a0nUz00000lVIX3IAO`

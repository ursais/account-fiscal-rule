# Avalara Certification Gap Plan

## Scope
- Module: `account_avatax_oca`
- Related OSI extension in stack: `mit_avatax_extended`
- Out of scope: core Odoo/Enterprise AvaTax modules

## Source Requirement
From `avalara_reqs.txt`:
- Mandatory: update `X-Avalara-Client` header to `Odoo;a0nUz00000lVIX3IAO`
- Recommendation: provide dynamic Avalara tax code retrieval via `ListTaxCodes`

## Identified Gaps
1. Client header used an outdated identifier.
2. Product tax codes were managed only as manual master data.
3. Module tests did not assert certification header or tax-code synchronization behavior.
4. No dedicated in-module markdown documentation for certification workstream.

## Implementation Plan
1. Enforce certified header in REST service bootstrap.
2. Add service method to fetch tax codes from Avalara SDK.
3. Add `action_sync_tax_codes` on AvaTax configuration to upsert `product.tax.code`.
4. Add tests for header enforcement and sync behavior.
5. Document changes and validation flow in `docs/*.md`.

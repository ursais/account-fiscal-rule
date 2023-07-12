# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _avatax_compute_tax(self):
        """Contact REST API and recompute taxes for a Sale Order"""
        """Override the Method Due to Taxes Issues faced in ORR Ticket Avatax Calculation - Split Taxable Lines for TN (#33258)"""
        self and self.ensure_one()
        doc_type = self._get_avatax_doc_type()
        Tax = self.env["account.tax"]
        avatax_config = self.company_id.get_avatax_config_company()
        if not avatax_config:
            return False
        partner = self.partner_id
        if avatax_config.use_partner_invoice_id:
            partner = self.partner_invoice_id
        taxable_lines = self._avatax_prepare_lines(self.order_line)
        tax_result = avatax_config.create_transaction(
            self.date_order,
            self.name,
            doc_type,
            partner,
            self.warehouse_id.partner_id or self.company_id.partner_id,
            self.tax_address_id or self.partner_id,
            taxable_lines,
            self.user_id,
            self.exemption_code or None,
            self.exemption_code_id.code or None,
            currency_id=self.currency_id,
            log_to_record=self,
        )
        tax_result_lines = {int(x["lineNumber"]): x for x in tax_result["lines"]}
        for line in self.order_line:
            tax_result_line = tax_result_lines.get(line.id)
            if tax_result_line:
                # Should we check the rate with the tax amount?
                # tax_amount = tax_result_line["taxCalculated"]
                # rate = round(tax_amount / line.price_subtotal * 100, 2)
                # rate = tax_result_line["rate"]
                tax_calculation = 0.0
                if tax_result_line["taxableAmount"]:
                    tax_calculation = (
                        tax_result_line["taxCalculated"]
                        / tax_result_line["taxableAmount"]
                    )
                rate = round(tax_calculation * 100, 4)
                tax = Tax.get_avalara_tax(rate, doc_type)
                if tax not in line.tax_id:
                    line_taxes = (
                        tax
                        if avatax_config.override_line_taxes
                        else tax | line.tax_id.filtered(lambda x: not x.is_avatax)
                    )
                    line.tax_id = line_taxes
                line.tax_amt = tax_result_line["tax"]
        self.tax_amount = tax_result.get("totalTax")
        return True

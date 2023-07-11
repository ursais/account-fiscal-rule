# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_scope_of_work = fields.Text("Scope of Work")
    po_required = fields.Boolean(string="PO Required")
    sale_customer_po = fields.Char("Customer PO")
    sale_customer_wo_number = fields.Char("Customer W/O Number")
    # This field is define temporary to avoid upgrade issue, This is in no use for ORR
    tax_exempt = fields.Boolean(
        "Is Tax Exempt",
        help="This company or address can claim for tax exemption",
    )
    orgn_fsm_order_id = fields.Many2one("fsm.order", string="Originating FSM Order")

    def _prepare_invoice(self):
        """Copy values from sale order to invoice"""
        vals = super(SaleOrder, self)._prepare_invoice()
        vals.update(
            {
                "invoice_scope_of_work": self.sale_scope_of_work,
                "invoice_customer_po": self.sale_customer_po,
                "invoice_customer_wo_number": self.sale_customer_wo_number,
                "partner_invoice_id": self.partner_invoice_id.id,
                "invoice_fsm_location_id": self.fsm_location_id.id,
            }
        )
        return vals

    def _field_create_fsm_order_prepare_values(self):
        result = super()._field_create_fsm_order_prepare_values()
        result.update({"scope_of_work": self.sale_scope_of_work})
        return result

    @api.onchange("partner_invoice_id")
    def _onchange_partner_invoice_id(self):
        res = super()._onchange_partner_invoice_id()
        po_required = False
        if self.partner_invoice_id:
            po_required = self.partner_invoice_id.po_required
        self.po_required = po_required
        return res

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

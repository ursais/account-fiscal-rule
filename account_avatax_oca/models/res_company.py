import logging

from odoo import _, models
from odoo.exceptions import RedirectWarning

_LOGGER = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = "res.company"

    def get_avatax_config_company(self):
        """Returns the AvaTax configuration for the Company"""
        if self:
            self.ensure_one()
            AvataxConfig = self.env["avalara.salestax"]
            res = AvataxConfig.search(
                [("company_id", "=", self.id), ("disable_tax_calculation", "=", False)]
            )
            if len(res) > 1:
                _LOGGER.warning(
                    _("Company %s has too many Avatax configurations!"),
                    self.display_name,
                )
            if len(res) < 1:
                _LOGGER.warning(
                    _("Company %s has no Avatax configuration."), self.display_name
                )
            return res and res[0]

    def _validate_fiscalyear_lock(self, values):
        res = super()._validate_fiscalyear_lock(values)
        avatax_config = self.get_avatax_config_company()
        if avatax_config.commit_to_avatax != "invoice_posting":
            uncommits_entries = self.env["account.move"].search(
                [
                    ("company_id", "in", self.ids),
                    ("move_type", "=", "out_invoice"),
                    ("committed_to_avatax", "=", False),
                    ("date", "<=", values["fiscalyear_lock_date"]),
                ]
            )
            if uncommits_entries:
                error_msg = _(
                    "There are still uncommitted Avatax entries in the period you want to lock. You should commit to Avatax before closing the fiscal year."
                )
                action_error = {
                    "view_mode": "tree",
                    "name": _("Uncommited Entries"),
                    "res_model": "account.move",
                    "type": "ir.actions.act_window",
                    "domain": [("id", "in", uncommits_entries.ids)],
                    "search_view_id": [
                        self.env.ref("account.view_account_move_filter").id,
                        "search",
                    ],
                    "views": [
                        [self.env.ref("account.view_move_tree").id, "list"],
                        [self.env.ref("account.view_move_form").id, "form"],
                    ],
                }
                raise RedirectWarning(
                    error_msg, action_error, _("Show uncommitted entries")
                )
        return res

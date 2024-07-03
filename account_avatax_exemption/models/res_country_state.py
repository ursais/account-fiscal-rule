from odoo import fields, models


class CountryState(models.Model):
    _inherit = "res.country.state"

    rule_ids = fields.One2many("exemption.code.rule", "state_id", "Avatax Rules")


class ResPartner(models.Model):
    _inherit = "res.partner"

    use_commercial_entity = fields.Boolean(compute="_compute_use_commercial_entity")

    def _compute_use_commercial_entity(self):
        avalara_salestax = self.env["avalara.salestax"].sudo().search([], limit=1)
        for partner in self:
            partner.use_commercial_entity = avalara_salestax.use_commercial_entity

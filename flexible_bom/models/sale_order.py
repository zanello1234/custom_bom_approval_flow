# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    flexible_bom_id = fields.Many2one(
        'mrp.bom',
        string='Custom BOM',
        help='Custom BOM created for this sale order line'
    )

    def action_create_flexible_bom(self):
        """Open wizard to create/edit flexible BOM"""
        self.ensure_one()
        
        if not self.product_id.is_flexible_bom:
            raise UserError("This product is not configured for Flexible BOM")
        
        # Check if order is confirmed and warn user
        warning_message = ""
        if self.state == 'sale':
            warning_message = ("⚠️ This sales order is already confirmed. "
                             "Creating or modifying the BOM may affect ongoing production. "
                             "Please coordinate with the production team.")
        
        # Get base BOM for the product with variant-specific priority
        # First, try to find a base BOM specific to this product variant
        base_bom = self.env['mrp.bom'].search([
            ('product_id', '=', self.product_id.id),  # Specific variant
            ('is_base_bom', '=', True),
            ('company_id', 'in', [self.company_id.id, False]),
            ('type', 'in', ['normal', 'phantom'])  # Support both Manufacturing and Kit BOMs
        ], limit=1)
        
        # If no variant-specific base BOM found, fallback to template-level base BOM
        if not base_bom:
            base_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('product_id', '=', False),  # Template level (no specific variant)
                ('is_base_bom', '=', True),
                ('company_id', 'in', [self.company_id.id, False]),
                ('type', 'in', ['normal', 'phantom'])  # Support both Manufacturing and Kit BOMs
            ], limit=1)
        
        if not base_bom:
            # Provide helpful error message
            if self.product_id.product_tmpl_id.product_variant_count > 1:
                raise UserError(
                    "No base BOM found for product variant '%s'. "
                    "Please create a base BOM either for this specific variant "
                    "or for the product template '%s'." % 
                    (self.product_id.display_name, self.product_id.product_tmpl_id.name)
                )
            else:
                raise UserError(
                    "No base BOM found for product '%s'. Please create a base BOM first." % 
                    self.product_id.name
                )
        
        # Determine wizard title based on order state
        wizard_title = 'Configure Flexible BOM'
        if self.state == 'sale':
            wizard_title = '⚠️ Modify Flexible BOM (Confirmed Order)'
        
        # Open wizard
        context = {
            'default_sale_order_line_id': self.id,
            'default_base_bom_id': base_bom.id,
            'default_product_id': self.product_id.id,
            'order_confirmed': self.state == 'sale',
            'warning_message': warning_message,
        }
        
        return {
            'name': wizard_title,
            'type': 'ir.actions.act_window',
            'res_model': 'flexible.bom.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': context
        }

    @api.depends('product_id', 'product_id.is_flexible_bom', 'state')
    def _compute_show_flexible_bom_button(self):
        for line in self:
            line.show_flexible_bom_button = (
                line.product_id and 
                line.product_id.is_flexible_bom and
                line.state in ('draft', 'sent', 'approved', 'bom_customization', 'sale')
            )

    show_flexible_bom_button = fields.Boolean(
        string='Show Flexible BOM Button',
        compute='_compute_show_flexible_bom_button'
    )

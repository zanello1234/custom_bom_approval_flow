# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_flexible_bom = fields.Boolean(
        string='Flexible BOM',
        default=False,
        help='Enable this option to allow creating custom BOM from sales order lines'
    )

    def action_setup_base_bom(self):
        """Action to setup base BOM for this product"""
        self.ensure_one()
        
        existing_boms = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.id),
            ('is_flexible_bom', '=', False)  # Only non-flexible BOMs can be base
        ])
        
        if not existing_boms:
            # Crear una nueva BOM base vacía para el producto
            new_bom = self.env['mrp.bom'].create({
                'product_tmpl_id': self.id,
                'is_base_bom': True,
                'type': 'normal',
                'is_flexible_bom': False,
                # No agregamos componentes
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Base BOM Creada',
                    'message': f'Se ha creado una BOM base vacía para el producto.',
                    'type': 'success',
                }
            }
        
        # If only one BOM exists, mark it as base automatically
        if len(existing_boms) == 1:
            existing_boms[0].is_base_bom = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Base BOM Set Successfully',
                    'message': f'BOM "{existing_boms[0].display_name}" has been marked as the base BOM for this product.',
                    'type': 'success',
                }
            }
        
        # If multiple BOMs exist, show wizard to select
        return {
            'type': 'ir.actions.act_window',
            'name': 'Setup Base BOM',
            'res_model': 'base.bom.setup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_tmpl_id': self.id,
            }
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.depends('product_tmpl_id.is_flexible_bom')
    def _compute_is_flexible_bom(self):
        for product in self:
            product.is_flexible_bom = product.product_tmpl_id.is_flexible_bom

    is_flexible_bom = fields.Boolean(
        string='Flexible BOM',
        compute='_compute_is_flexible_bom',
        store=True,
        help='Enable this option to allow creating custom BOM from sales order lines'
    )

    def action_setup_base_bom(self):
        """Action to setup base BOM for this product - delegates to template"""
        return self.product_tmpl_id.action_setup_base_bom()

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BaseBomSetupWizard(models.TransientModel):
    _name = 'base.bom.setup.wizard'
    _description = 'Setup Base BOM Wizard'

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True
    )
    
    existing_bom_ids = fields.One2many(
        'base.bom.setup.line',
        'wizard_id',
        string='Existing BOMs'
    )
    
    selected_base_bom_id = fields.Many2one(
        'mrp.bom',
        string='Select Base BOM',
        required=True,
        help='This BOM will be used as template for flexible BOMs and manufacturing orders'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        if 'product_tmpl_id' in fields_list:
            product_tmpl_id = self.env.context.get('default_product_tmpl_id')
            if product_tmpl_id:
                res['product_tmpl_id'] = product_tmpl_id
                
                # Load existing BOMs
                existing_boms = self.env['mrp.bom'].search([
                    ('product_tmpl_id', '=', product_tmpl_id),
                    ('is_flexible_bom', '=', False)  # Only show non-flexible BOMs as candidates
                ])
                
                bom_lines = []
                current_base = None
                
                for bom in existing_boms:
                    bom_lines.append((0, 0, {
                        'bom_id': bom.id,
                        'is_current_base': bom.is_base_bom
                    }))
                    if bom.is_base_bom:
                        current_base = bom.id
                
                res['existing_bom_ids'] = bom_lines
                if current_base:
                    res['selected_base_bom_id'] = current_base
                elif existing_boms:
                    # Default to oldest BOM
                    res['selected_base_bom_id'] = existing_boms.sorted('create_date')[0].id
        
        return res

    def action_set_base_bom(self):
        """Set the selected BOM as base and unmark others"""
        self.ensure_one()
        
        if not self.selected_base_bom_id:
            raise UserError(_("Please select a BOM to mark as base."))
        
        # Unmark all current base BOMs for this product
        existing_bases = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('is_base_bom', '=', True)
        ])
        existing_bases.write({'is_base_bom': False})
        
        # Mark selected BOM as base
        self.selected_base_bom_id.is_base_bom = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Base BOM Updated Successfully',
                'message': f'BOM "{self.selected_base_bom_id.display_name}" is now the base BOM for {self.product_tmpl_id.name}.',
                'type': 'success',
            }
        }


class BaseBomSetupLine(models.TransientModel):
    _name = 'base.bom.setup.line'
    _description = 'Base BOM Setup Line'

    wizard_id = fields.Many2one(
        'base.bom.setup.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    bom_id = fields.Many2one(
        'mrp.bom',
        string='BOM',
        required=True
    )
    
    is_current_base = fields.Boolean(
        string='Current Base',
        help='This BOM is currently marked as base'
    )
    
    bom_code = fields.Char(
        related='bom_id.code',
        string='BOM Code'
    )
    
    bom_type = fields.Selection(
        related='bom_id.type',
        string='Type'
    )
    
    component_count = fields.Integer(
        string='Components',
        compute='_compute_component_count'
    )

    @api.depends('bom_id')
    def _compute_component_count(self):
        for line in self:
            line.component_count = len(line.bom_id.bom_line_ids)

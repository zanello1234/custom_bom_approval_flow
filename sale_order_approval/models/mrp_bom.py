# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.model
    def _bom_find(self, product_tmpl=None, product=None, company_id=False, bom_type=False):
        """
        Override BOM search to prioritize flexible BOMs when in sale order context
        """
        # First check if we're in a context where flexible BOM should be used
        sale_line_id = self.env.context.get('sale_line_id')
        flexible_bom_id = self.env.context.get('flexible_bom_id')
        
        if flexible_bom_id:
            flexible_bom = self.browse(flexible_bom_id)
            if flexible_bom.exists():
                _logger.info(f"🎯 Using flexible BOM from context: {flexible_bom.display_name}")
                return flexible_bom
        
        if sale_line_id:
            sale_line = self.env['sale.order.line'].browse(sale_line_id)
            if sale_line.exists() and hasattr(sale_line, 'flexible_bom_id') and sale_line.flexible_bom_id:
                # Check if the flexible BOM matches the product we're looking for
                if sale_line.flexible_bom_id.product_id == product or sale_line.flexible_bom_id.product_tmpl_id == product_tmpl:
                    _logger.info(f"🎯 Using flexible BOM from sale line: {sale_line.flexible_bom_id.display_name}")
                    return sale_line.flexible_bom_id
        
        # If no flexible BOM context, use standard logic
        return super()._bom_find(product_tmpl=product_tmpl, product=product, company_id=company_id, bom_type=bom_type)

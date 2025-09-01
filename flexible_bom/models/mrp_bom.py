# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    is_flexible_bom = fields.Boolean(
        string='Flexible BOM',
        default=False,
        help='This BOM was created from a sales order line'
    )
    
    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Sales Order Line',
        help='Sales order line this BOM was created from'
    )
    
    base_bom_id = fields.Many2one(
        'mrp.bom',
        string='Base BOM',
        help='Original BOM used as template for this flexible BOM'
    )
    
    is_base_bom = fields.Boolean(
        string='Is Base BOM',
        default=False,
        help='This BOM serves as a template for flexible BOM creation'
    )

    # Note: SQL EXCLUDE constraint might not be supported in all PostgreSQL versions
    # Using Python validation instead for better compatibility
    _sql_constraints = [
        ('check_not_flexible_and_base', 
         'CHECK (NOT (is_flexible_bom = true AND is_base_bom = true))',
         'A BOM cannot be both flexible and base!'),
    ]

    @api.constrains('is_base_bom', 'product_id', 'product_tmpl_id')
    def _check_unique_base_bom(self):
        """Ensure only one base BOM per product variant (or template if no specific variant)"""
        for bom in self:
            if bom.is_base_bom:
                # If BOM is for a specific variant, check uniqueness by product_id
                if bom.product_id:
                    existing_base_boms = self.search([
                        ('product_id', '=', bom.product_id.id),
                        ('is_base_bom', '=', True),
                        ('id', '!=', bom.id)
                    ])
                    if existing_base_boms:
                        raise ValidationError(_(
                            'There is already a base BOM for product variant "%s". '
                            'Only one base BOM is allowed per product variant. '
                            'Existing base BOM: %s'
                        ) % (bom.product_id.display_name, existing_base_boms[0].display_name))
                else:
                    # If BOM is for template (all variants), check uniqueness by product_tmpl_id
                    existing_base_boms = self.search([
                        ('product_tmpl_id', '=', bom.product_tmpl_id.id),
                        ('product_id', '=', False),  # Only template-level BOMs
                        ('is_base_bom', '=', True),
                        ('id', '!=', bom.id)
                    ])
                    if existing_base_boms:
                        raise ValidationError(_(
                            'There is already a base BOM for product template "%s" (template level). '
                            'Only one base BOM is allowed per product template. '
                            'Existing base BOM: %s'
                        ) % (bom.product_tmpl_id.name, existing_base_boms[0].display_name))

    @api.constrains('is_flexible_bom', 'is_base_bom')
    def _check_flexible_not_base(self):
        """Ensure flexible BOMs cannot be base BOMs"""
        for bom in self:
            if bom.is_flexible_bom and bom.is_base_bom:
                raise ValidationError(_(
                    'A BOM cannot be both flexible and base. '
                    'Flexible BOMs are derived from base BOMs.'
                ))

    flexible_bom_count = fields.Integer(
        string='Flexible BOMs Created',
        compute='_compute_flexible_bom_count',
        help='Number of flexible BOMs created from this base BOM'
    )

    @api.depends('is_base_bom')
    def _compute_flexible_bom_count(self):
        for bom in self:
            if bom.is_base_bom:
                bom.flexible_bom_count = self.search_count([('base_bom_id', '=', bom.id)])
            else:
                bom.flexible_bom_count = 0

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle base BOM logic"""
        boms = super().create(vals_list)
        
        for bom in boms:
            # If this is a flexible BOM and we have a base BOM set, mark it as base
            if bom.is_flexible_bom and bom.base_bom_id:
                bom.base_bom_id.is_base_bom = True
            elif bom.is_flexible_bom and not bom.base_bom_id:
                # If this is a flexible BOM and we don't have a base BOM set,
                # try to find and mark the appropriate base BOM
                base_bom = self._find_base_bom_for_product(bom.product_tmpl_id)
                if base_bom:
                    bom.base_bom_id = base_bom.id
                    base_bom.is_base_bom = True
        
        return boms

    def write(self, vals):
        """Override write to handle base BOM validation"""
        # If trying to mark as base BOM, validate uniqueness
        if vals.get('is_base_bom'):
            for bom in self:
                if bom.is_flexible_bom:
                    raise ValidationError(_("Flexible BOMs cannot be marked as base BOMs."))
                
                existing_base_bom = self.search([
                    ('product_tmpl_id', '=', bom.product_tmpl_id.id),
                    ('is_base_bom', '=', True),
                    ('id', '!=', bom.id)
                ], limit=1)
                
                if existing_base_bom:
                    raise ValidationError(_(
                        'There is already a base BOM for product "%s" (BOM: %s). '
                        'Only one base BOM is allowed per product template. '
                        'Use "Replace Base BOM" action if you want to replace it.'
                    ) % (bom.product_tmpl_id.name, existing_base_bom.display_name))
        
        return super().write(vals)

    def _find_base_bom_for_product(self, product_tmpl):
        """Find the most appropriate base BOM for a product"""
        # Look for existing base BOM
        base_bom = self.search([
            ('product_tmpl_id', '=', product_tmpl.id),
            ('is_base_bom', '=', True),
            ('is_flexible_bom', '=', False)
        ], limit=1)
        
        if base_bom:
            return base_bom
        
        # If no base BOM exists, find the oldest non-flexible BOM
        oldest_bom = self.search([
            ('product_tmpl_id', '=', product_tmpl.id),
            ('is_flexible_bom', '=', False),
            ('company_id', 'in', [self.env.company.id, False])
        ], order='create_date asc', limit=1)
        
        if oldest_bom:
            oldest_bom.is_base_bom = True
            return oldest_bom
        
        return False

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle base BOM logic"""
        boms = super().create(vals_list)
        
        for bom in boms:
            # If this is a flexible BOM and we have a base BOM set, mark it as base
            if bom.is_flexible_bom and bom.base_bom_id:
                bom.base_bom_id.is_base_bom = True
            elif bom.is_flexible_bom and not bom.base_bom_id:
                # If this is a flexible BOM and we don't have a base BOM set,
                # try to find and mark the appropriate base BOM
                base_bom = self._find_base_bom_for_product(bom.product_tmpl_id)
                if base_bom:
                    bom.base_bom_id = base_bom.id
                    base_bom.is_base_bom = True
            elif not bom.is_flexible_bom and not bom.is_base_bom:
                # For new non-flexible BOMs, check if we should mark as base
                existing_base = self.search([
                    ('product_tmpl_id', '=', bom.product_tmpl_id.id),
                    ('is_base_bom', '=', True)
                ], limit=1)
                if not existing_base:
                    # No base BOM exists for this product, mark this as base
                    bom.is_base_bom = True
        
        return boms

    def _find_base_bom_for_product(self, product_tmpl):
        """Find the most appropriate base BOM for a product"""
        # Look for existing base BOM
        base_bom = self.search([
            ('product_tmpl_id', '=', product_tmpl.id),
            ('is_base_bom', '=', True),
            ('is_flexible_bom', '=', False)
        ], limit=1)
        
        if base_bom:
            return base_bom
        
        # If no base BOM exists, find the oldest non-flexible BOM
        oldest_bom = self.search([
            ('product_tmpl_id', '=', product_tmpl.id),
            ('is_flexible_bom', '=', False),
            ('company_id', 'in', [self.env.company.id, False])
        ], order='create_date asc', limit=1)
        
        if oldest_bom:
            oldest_bom.is_base_bom = True
            return oldest_bom
        
        return False

    @api.model
    def _bom_find(self, products, **kwargs):
        """Override to prefer base BOMs for manufacturing orders"""
        # First get the standard result
        result = super()._bom_find(products, **kwargs)
        
        # Aggressive validation and singleton enforcement
        if result and not isinstance(result, dict):
            # Single BOM result should be singleton
            if hasattr(result, 'ids') and len(result.ids) > 1:
                _logger.warning(f"_bom_find parent method returned multiple BOMs: {result.ids}. Taking first one.")
                result = result[0]
                result.ensure_one()  # Validate singleton
        elif isinstance(result, dict):
            # Dictionary result - validate each BOM is singleton
            for product, bom in result.items():
                if bom and hasattr(bom, 'ids') and len(bom.ids) > 1:
                    _logger.warning(f"_bom_find parent method returned multiple BOMs for product {product.id}: {bom.ids}. Taking first one.")
                    result[product] = bom[0]
                    result[product].ensure_one()  # Validate singleton
        
        # Extract parameters
        bom_type = kwargs.get('bom_type', 'normal')
        company_id = kwargs.get('company_id', False)
        
        # Only override for normal manufacturing orders, not phantom BOMs
        if bom_type == 'phantom':
            return result
            
        # Ensure we have a products recordset
        if not hasattr(products, 'ids'):
            products = self.env['product.product'].browse(products.id if hasattr(products, 'id') else products)
        
        # Handle dictionary result (multiple products)
        if isinstance(result, dict):
            enhanced_result = {}
            
            # Ensure all products are in the result, even if no BOM was found
            for product in products:
                original_bom = result.get(product, False)
                
                # Try to find base BOM for this product
                base_bom = self.search([
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('is_base_bom', '=', True),
                    ('company_id', 'in', [company_id or self.env.company.id, False]),
                    ('type', '=', bom_type)
                ], limit=1)
                
                # Ensure singleton result
                if base_bom:
                    base_bom.ensure_one()  # Validate it's a singleton
                    enhanced_result[product] = base_bom
                elif original_bom and hasattr(original_bom, 'is_flexible_bom') and not original_bom.is_flexible_bom:
                    # Ensure original_bom is also singleton before marking
                    if hasattr(original_bom, 'ensure_one'):
                        original_bom.ensure_one()
                    # Mark existing BOM as base
                    original_bom.is_base_bom = True
                    enhanced_result[product] = original_bom
                else:
                    # Use empty recordset instead of False to prevent AttributeError
                    enhanced_result[product] = original_bom if original_bom else self.env['mrp.bom']
            
            # Final validation: ensure all values are singleton or empty
            for product, bom in enhanced_result.items():
                if bom and hasattr(bom, 'ids') and len(bom.ids) > 1:
                    _logger.error(f"Final validation failed: multiple BOMs for product {product.id}: {bom.ids}. Forcing singleton.")
                    enhanced_result[product] = bom[0]
                    enhanced_result[product].ensure_one()
            
            return enhanced_result
        
        # Handle single product/BOM result
        else:
            if len(products) == 1:
                product = products[0]
                
                # Try to find base BOM for this product
                base_bom = self.search([
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('is_base_bom', '=', True),
                    ('company_id', 'in', [company_id or self.env.company.id, False]),
                    ('type', '=', bom_type)
                ], limit=1)
                
                if base_bom:
                    base_bom.ensure_one()  # Validate it's a singleton
                    return base_bom
                elif result and hasattr(result, 'is_flexible_bom') and not result.is_flexible_bom:
                    # Ensure result is singleton before marking
                    if hasattr(result, 'ensure_one'):
                        result.ensure_one()
                    # Mark existing BOM as base
                    result.is_base_bom = True
                
                # Final validation for single product result
                if result and hasattr(result, 'ids') and len(result.ids) > 1:
                    _logger.error(f"Final validation failed for single product {product.id}: multiple BOMs {result.ids}. Forcing singleton.")
                    result = result[0]
                    result.ensure_one()
                
                return result
            else:
                # Multiple products but got single result - shouldn't happen, return as-is
                return result

    def mark_as_base_bom(self):
        """Action to manually mark a BOM as base BOM"""
        for bom in self:
            if bom.is_flexible_bom:
                raise UserError(_("Flexible BOMs cannot be marked as base BOMs."))
            
            # Check if there's already a base BOM for this product
            existing_base_bom = self.search([
                ('product_tmpl_id', '=', bom.product_tmpl_id.id),
                ('is_base_bom', '=', True),
                ('id', '!=', bom.id)
            ], limit=1)
            
            if existing_base_bom:
                # Ask user what to do with existing base BOM
                raise UserError(_(
                    'There is already a base BOM for product "%s" (BOM: %s). '
                    'Only one base BOM is allowed per product. '
                    'Please first unmark the existing base BOM or use the replacement function.'
                ) % (bom.product_tmpl_id.name, existing_base_bom.display_name))
            
            # Mark this as base BOM
            bom.is_base_bom = True

    def replace_as_base_bom(self):
        """Replace existing base BOM with this one"""
        for bom in self:
            if bom.is_flexible_bom:
                raise UserError(_("Flexible BOMs cannot be marked as base BOMs."))
            
            # Unmark any existing base BOM for this product
            existing_base_boms = self.search([
                ('product_tmpl_id', '=', bom.product_tmpl_id.id),
                ('is_base_bom', '=', True),
                ('id', '!=', bom.id)
            ])
            
            if existing_base_boms:
                existing_base_boms.write({'is_base_bom': False})
                
            # Mark this as base BOM
            bom.is_base_bom = True
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Base BOM Updated'),
                    'message': _('BOM "%s" is now the base BOM for product "%s"') % (
                        bom.display_name, 
                        bom.product_tmpl_id.name
                    ),
                    'type': 'success',
                }
            }

    def unmark_as_base_bom(self):
        """Action to unmark a BOM as base BOM"""
        self.write({'is_base_bom': False})

    @api.model
    def cleanup_duplicate_base_boms(self):
        """Utility method to clean up duplicate base BOMs"""
        _logger.info("Starting cleanup of duplicate base BOMs...")
        
        # Clean up duplicate base BOMs at template level (product_id = False)
        self.env.cr.execute("""
            SELECT product_tmpl_id, COUNT(*) as count
            FROM mrp_bom 
            WHERE is_base_bom = true AND product_id IS NULL
            GROUP BY product_tmpl_id 
            HAVING COUNT(*) > 1
        """)
        
        duplicate_templates = self.env.cr.fetchall()
        
        for product_tmpl_id, count in duplicate_templates:
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
            _logger.info(f"Cleaning duplicate template-level base BOMs for: {product_tmpl.name} ({count} BOMs)")
            
            # Get all template-level base BOMs for this product
            base_boms = self.search([
                ('product_tmpl_id', '=', product_tmpl_id),
                ('product_id', '=', False),  # Template level only
                ('is_base_bom', '=', True)
            ], order='create_date asc')
            
            # Keep only the oldest one as base
            if len(base_boms) > 1:
                bom_to_keep = base_boms[0]
                boms_to_unmark = base_boms[1:]
                
                _logger.info(f"Keeping template BOM {bom_to_keep.display_name} as base, unmarking {len(boms_to_unmark)} others")
                boms_to_unmark.write({'is_base_bom': False})
        
        # Clean up duplicate base BOMs at variant level (same product_id)
        self.env.cr.execute("""
            SELECT product_id, COUNT(*) as count
            FROM mrp_bom 
            WHERE is_base_bom = true AND product_id IS NOT NULL
            GROUP BY product_id 
            HAVING COUNT(*) > 1
        """)
        
        duplicate_variants = self.env.cr.fetchall()
        
        for product_id, count in duplicate_variants:
            product = self.env['product.product'].browse(product_id)
            _logger.info(f"Cleaning duplicate variant-level base BOMs for: {product.display_name} ({count} BOMs)")
            
            # Get all variant-level base BOMs for this product
            base_boms = self.search([
                ('product_id', '=', product_id),
                ('is_base_bom', '=', True)
            ], order='create_date asc')
            
            # Keep only the oldest one as base
            if len(base_boms) > 1:
                bom_to_keep = base_boms[0]
                boms_to_unmark = base_boms[1:]
                
                _logger.info(f"Keeping variant BOM {bom_to_keep.display_name} as base, unmarking {len(boms_to_unmark)} others")
                boms_to_unmark.write({'is_base_bom': False})
        
        if not duplicate_templates and not duplicate_variants:
            _logger.info("No duplicate base BOMs found.")
        
        _logger.info("Cleanup of duplicate base BOMs completed.")
        return True

    @api.model
    def _run_integrity_check_and_cleanup(self):
        """Run integrity check and cleanup. Can be called manually or automatically."""
        _logger.info("Starting integrity check and cleanup...")
        
        # First, cleanup duplicates
        self.cleanup_duplicate_base_boms()
        
        # Then validate integrity
        issues = self.validate_base_bom_integrity()
        if issues:
            _logger.warning(f"Integrity issues found after cleanup: {issues}")
        else:
            _logger.info("No integrity issues found after cleanup.")
            
        return not bool(issues)  # Return True if no issues

    @api.model
    def validate_base_bom_integrity(self):
        """Validate that base BOM rules are followed throughout the system"""
        issues = []
        
        # Check for multiple base BOMs per product
        self.env.cr.execute("""
            SELECT product_tmpl_id, COUNT(*) as count
            FROM mrp_bom 
            WHERE is_base_bom = true 
            GROUP BY product_tmpl_id 
            HAVING COUNT(*) > 1
        """)
        
        duplicate_products = self.env.cr.fetchall()
        for product_tmpl_id, count in duplicate_products:
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
            issues.append(f"Product '{product_tmpl.name}' has {count} base BOMs (should be 1)")
        
        # Check for flexible BOMs marked as base
        flexible_base_boms = self.search([
            ('is_flexible_bom', '=', True),
            ('is_base_bom', '=', True)
        ])
        
        for bom in flexible_base_boms:
            issues.append(f"BOM '{bom.display_name}' is marked as both flexible and base (invalid)")
        
        # Check for flexible BOMs without base_bom_id
        flexible_without_base = self.search([
            ('is_flexible_bom', '=', True),
            ('base_bom_id', '=', False)
        ])
        
        for bom in flexible_without_base:
            issues.append(f"Flexible BOM '{bom.display_name}' has no base BOM reference")
            
        return issues

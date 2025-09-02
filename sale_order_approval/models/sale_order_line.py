# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_all_kit_components(self, product, bom, qty=1.0):
        """
        Recursively expand BOM to get all leaf components for KIT type BOMs.
        Returns a list of tuples (component_product, total_quantity)
        """
        components = []
        
        if not bom:
            return [(product, qty)]
        
        # If BOM is not KIT type, return the product itself
        if bom.type != 'phantom':  # phantom = KIT in Odoo
            return [(product, qty)]
        
        _logger.info(f"Expanding KIT BOM {bom.display_name} for product {product.display_name}")
        
        for line in bom.bom_line_ids:
            component_product = line.product_id
            component_qty = line.product_qty * qty
            
            # Check if this component has its own BOM
            component_bom = self.env['mrp.bom']._bom_find(
                component_product,
                company_id=self.company_id.id,
                bom_type='phantom'  # Only look for KIT BOMs
            )
            
            if component_bom and component_bom.type == 'phantom':
                # Recursively expand this component's BOM
                sub_components = self._get_all_kit_components(
                    component_product, 
                    component_bom, 
                    component_qty
                )
                components.extend(sub_components)
            else:
                # This is a leaf component
                components.append((component_product, component_qty))
        
        return components

    def _action_launch_stock_rule(self):
        """
        Override to handle KIT BOM expansion for deliveries.
        When a product has a KIT BOM with sub-KIT components, 
        create delivery for all leaf components instead.
        """
        _logger.info(f"Launching stock rule for sale line {self.id} - Product: {self.product_id.display_name}")
        
        # Get the BOM for this product
        bom = self.env['mrp.bom']._bom_find(
            self.product_id,
            company_id=self.company_id.id
        )
        
        if bom and bom.type == 'phantom':  # KIT BOM
            _logger.info(f"Found KIT BOM {bom.display_name} for product {self.product_id.display_name}")
            
            # Get all leaf components
            all_components = self._get_all_kit_components(
                self.product_id, 
                bom, 
                self.product_uom_qty
            )
            
            if all_components:
                _logger.info(f"Expanded KIT to {len(all_components)} leaf components")
                
                # Create stock moves for each leaf component instead of the main product
                self._create_kit_stock_moves(all_components)
                return
        
        # If not a KIT or no BOM, use standard behavior
        return super()._action_launch_stock_rule()

    def _create_kit_stock_moves(self, components):
        """
        Create stock moves for KIT components.
        components: list of tuples (product, quantity)
        """
        _logger.info(f"Creating stock moves for {len(components)} KIT components")
        
        # Get the warehouse and location info
        warehouse = self.order_id._get_warehouse()
        if not warehouse:
            _logger.error("No warehouse found for sale order")
            return
        
        # Group components by product to avoid duplicates
        component_dict = {}
        for product, qty in components:
            if product.id in component_dict:
                component_dict[product.id]['qty'] += qty
            else:
                component_dict[product.id] = {
                    'product': product,
                    'qty': qty
                }
        
        # Create a delivery order for the components
        picking_vals = {
            'partner_id': self.order_id.partner_shipping_id.id,
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'location_dest_id': self.order_id.partner_shipping_id.property_stock_customer.id,
            'origin': self.order_id.name,
            'move_type': 'direct',
        }
        
        picking = self.env['stock.picking'].create(picking_vals)
        _logger.info(f"Created picking {picking.name} for KIT components")
        
        # Create stock moves for each component
        for component_data in component_dict.values():
            product = component_data['product']
            qty = component_data['qty']
            
            move_vals = {
                'name': f"{self.order_id.name} - {product.display_name}",
                'product_id': product.id,
                'product_uom_qty': qty,
                'product_uom': product.uom_id.id,
                'picking_id': picking.id,
                'location_id': warehouse.out_type_id.default_location_src_id.id,
                'location_dest_id': self.order_id.partner_shipping_id.property_stock_customer.id,
                'sale_line_id': self.id,
                'origin': self.order_id.name,
            }
            
            move = self.env['stock.move'].create(move_vals)
            _logger.info(f"Created stock move for {product.display_name} - Qty: {qty}")
        
        # Confirm the picking to make it available
        picking.action_confirm()
        _logger.info(f"Confirmed picking {picking.name}")

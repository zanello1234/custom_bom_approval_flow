# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class FlexibleBomWizard(models.TransientModel):
    _name = 'flexible.bom.wizard'
    _description = 'Flexible BOM Configuration Wizard'

    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Sales Order Line',
        required=True
    )
    
    base_bom_id = fields.Many2one(
        'mrp.bom',
        string='Base BOM',
        required=True
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    
    bom_type = fields.Selection([
        ('normal', 'Manufacture this product'),
        ('phantom', 'Kit')
    ], string='BOM Type', default='normal', required=True,
    help="- Manufacture this product: The product is manufactured or assembled from the components.\n"
         "- Kit: The product is distributed as a set of components.")
    
    bom_line_ids = fields.One2many(
        'flexible.bom.line.wizard',
        'wizard_id',
        string='BOM Lines'
    )
    
    routing_line_ids = fields.One2many(
        'flexible.bom.routing.wizard',
        'wizard_id',
        string='Routing Lines'
    )
    
    order_confirmed = fields.Boolean(
        string='Order Confirmed',
        default=False,
        help='Indicates if the sales order is already confirmed'
    )
    
    cancel_existing_deliveries = fields.Boolean(
        string='Cancelar y Recrear Entregas Existentes',
        default=True,
        help='Si está marcado, las entregas existentes se cancelarán y recrearán basándose en el nuevo BOM. '
             'Si no está marcado, las entregas permanecerán como están (no recomendado para cambios importantes de BOM).'
    )
    
    warning_message = fields.Text(
        string='Warning Message',
        help='Warning message for confirmed orders'
    )
    
    delivery_warning = fields.Text(
        string='Delivery Warning',
        help='Warning message about delivery management'
    )
    
    base_bom_info = fields.Text(
        string='Base BOM Information',
        compute='_compute_base_bom_info',
        help='Information about which base BOM is being used'
    )

    @api.depends('base_bom_id', 'product_id')
    def _compute_base_bom_info(self):
        """Compute information about the base BOM being used"""
        for wizard in self:
            if wizard.base_bom_id and wizard.product_id:
                base_bom = wizard.base_bom_id
                info_parts = []
                
                # Determine if it's variant-specific or template-level
                if base_bom.product_id:
                    info_parts.append(f"🎯 BOM específica para la variante: {base_bom.product_id.display_name}")
                else:
                    info_parts.append(f"📋 BOM a nivel de template: {base_bom.product_tmpl_id.name}")
                
                # Add BOM type info
                bom_type_name = 'Kit' if base_bom.type == 'phantom' else 'Manufactura'
                info_parts.append(f"Tipo: {bom_type_name}")
                
                # Add component count
                component_count = len(base_bom.bom_line_ids)
                info_parts.append(f"Componentes: {component_count}")
                
                wizard.base_bom_info = ' | '.join(info_parts)
            else:
                wizard.base_bom_info = "No hay BOM base seleccionada"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        _logger.info(f"=== DEFAULT_GET DEBUG ===")
        _logger.info(f"Context: {self.env.context}")
        _logger.info(f"Fields list: {fields_list}")
        _logger.info(f"Initial res: {res}")
        
        # Handle confirmed order context
        context = self.env.context
        if context.get('order_confirmed'):
            res['order_confirmed'] = True
        if context.get('warning_message'):
            res['warning_message'] = context.get('warning_message')
            
        # Ensure cancel_existing_deliveries has a default value
        if 'cancel_existing_deliveries' in fields_list and 'cancel_existing_deliveries' not in res:
            res['cancel_existing_deliveries'] = True
            _logger.info("Set cancel_existing_deliveries default to True")
            
        _logger.info(f"Final res: {res}")
        
        if 'base_bom_id' in res and res.get('base_bom_id'):
            base_bom = self.env['mrp.bom'].browse(res['base_bom_id'])
            
            # Set BOM type based on base BOM
            res['bom_type'] = base_bom.type
            
            # Load BOM lines
            bom_lines = []
            for line in base_bom.bom_line_ids:
                bom_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'product_uom_id': line.product_uom_id.id,
                    'sequence': line.sequence,
                }))
            res['bom_line_ids'] = bom_lines
            
            # Load routing lines  
            routing_lines = []
            # Skip routing lines for now as Odoo 18 may handle BOMs differently
            # This will be empty by default, which is fine for basic functionality
            res['routing_line_ids'] = routing_lines
            
        return res

    @api.onchange('cancel_existing_deliveries')
    def _onchange_cancel_existing_deliveries(self):
        """Track changes to the cancel_existing_deliveries field"""
        _logger.info(f"=== ONCHANGE DELIVERY TOGGLE ===")
        _logger.info(f"New value: {self.cancel_existing_deliveries}")
        _logger.info(f"Type: {type(self.cancel_existing_deliveries)}")
        
        if hasattr(self, 'order_confirmed') and self.order_confirmed:
            if self.cancel_existing_deliveries:
                _logger.info("User enabled automatic delivery cancellation")
            else:
                _logger.info("User disabled automatic delivery cancellation")

    @api.onchange('bom_type')
    def _onchange_bom_type(self):
        """Show different help text based on BOM type"""
        if self.bom_type == 'phantom':
            return {
                'warning': {
                    'title': 'Kit BOM Selected',
                    'message': 'Kit BOMs do not require manufacturing operations. The components will be delivered as separate items to the customer.'
                }
            }

    def action_create_bom(self):
        """Create the flexible BOM and associate it with the sale order line"""
        self.ensure_one()
        
        _logger.info(f"=== Starting BOM creation ===")
        _logger.info(f"Product: {self.product_id.name}")
        _logger.info(f"Order confirmed: {self.order_confirmed}")
        _logger.info(f"Cancel existing deliveries: {self.cancel_existing_deliveries}")
        _logger.info(f"Sale order line: {self.sale_order_line_id.id}")
        
        # Special handling for confirmed orders
        if self.order_confirmed:
            # Check if there are existing manufacturing orders
            existing_mos = self.env['mrp.production'].search([
                ('origin', '=', self.sale_order_line_id.order_id.name),
                ('product_id', '=', self.product_id.id),
                ('state', 'not in', ['done', 'cancel'])
            ])
            
            if existing_mos:
                # Create warning message about existing MOs
                mo_list = ', '.join(existing_mos.mapped('name'))
                warning_msg = (f"⚠️ ATTENTION: There are existing manufacturing orders for this product: {mo_list}. "
                             f"Creating a new BOM will not affect these existing orders. "
                             f"You may need to manually update them if necessary.")
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Existing Manufacturing Orders Found',
                        'message': warning_msg,
                        'type': 'warning',
                        'sticky': True,
                    }
                }
        
        # Create new BOM
        bom_code = f"{self.sale_order_line_id.order_id.name}: {self.product_id.name}"
        if self.order_confirmed:
            bom_code += " (Modified)"
        bom_code += f" ({'Kit' if self.bom_type == 'phantom' else 'Manufacturing'})"
        
        bom_vals = {
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'product_id': self.product_id.id,
            'product_qty': 1.0,
            'type': self.bom_type,
            'is_flexible_bom': True,
            'sale_order_line_id': self.sale_order_line_id.id,
            'base_bom_id': self.base_bom_id.id,
            'code': bom_code,
        }
        
        # Create routing if needed (simplified for Odoo 18 compatibility)
        # For now, we'll skip routing creation to avoid compatibility issues
        # This can be enhanced later once we understand Odoo 18's routing structure better
        
        new_bom = self.env['mrp.bom'].create(bom_vals)
        
        # Create BOM lines
        for bom_line in self.bom_line_ids:
            self.env['mrp.bom.line'].create({
                'bom_id': new_bom.id,
                'product_id': bom_line.product_id.id,
                'product_qty': bom_line.product_qty,
                'product_uom_id': bom_line.product_uom_id.id,
                'sequence': bom_line.sequence,
            })
        
        # Update sale order line
        _logger.info(f"🔗 Assigning flexible BOM {new_bom.id} ({new_bom.display_name}) to sale order line {self.sale_order_line_id.id}")
        self.sale_order_line_id.flexible_bom_id = new_bom.id
        _logger.info(f"✅ Sale order line {self.sale_order_line_id.id} now has flexible_bom_id: {self.sale_order_line_id.flexible_bom_id}")
        
        # Handle delivery cancellation and recreation for confirmed orders
        delivery_message = ""
        _logger.info(f"=== DELIVERY HANDLING ===")
        _logger.info(f"self.order_confirmed = {self.order_confirmed}")
        
        if self.order_confirmed:
            _logger.info("Order confirmed, automatically updating deliveries...")
            try:
                delivery_message = self._handle_delivery_update()
                _logger.info(f"Delivery update completed with message: {delivery_message}")
            except Exception as e:
                error_msg = f"Error durante actualización de entregas: {str(e)}"
                _logger.error(error_msg)
                delivery_message = error_msg
        else:
            _logger.info("Order not confirmed, skipping delivery handling")
        
        # Handle price updates differently for confirmed orders
        if self.order_confirmed:
            # For confirmed orders, show notification and close window
            full_message = f'BOM Flexible "{new_bom.code}" ha sido creado. Para órdenes confirmadas, los precios no se actualizan automáticamente. Por favor, revise y ajuste manualmente si es necesario.'
            if delivery_message:
                full_message += f'\n\n{delivery_message}'
                
            # Show notification using message_post and close window
            self.sale_order_line_id.order_id.message_post(
                body=f"✅ {full_message}",
                message_type='notification'
            )
            return {'type': 'ir.actions.act_window_close'}
        else:
            # For draft orders, update price automatically and close window
            self._update_sale_line_price()
            return {'type': 'ir.actions.act_window_close'}

    def _update_sale_line_price(self):
        """Update sale order line price based on BOM components"""
        total_cost = 0.0
        
        for bom_line in self.bom_line_ids:
            component_cost = bom_line.product_id.standard_price * bom_line.product_qty
            total_cost += component_cost
        
        # Add margin (you can make this configurable)
        margin = 1.2  # 20% margin
        new_price = total_cost * margin
        
        self.sale_order_line_id.price_unit = new_price

    def _handle_delivery_update(self):
        """Handle delivery cancellation and recreation when BOM is updated"""
        _logger.info(f"=== DELIVERY UPDATE HANDLER ===")
        _logger.info(f"Sale order line: {self.sale_order_line_id.id}")
        
        order = self.sale_order_line_id.order_id
        _logger.info(f"Processing sale order: {order.name}")
        
        delivery_info = []
        
        try:
            # Step 1: Cancel all existing deliveries for this order
            existing_pickings = self.env['stock.picking'].search([
                ('origin', '=', order.name),
                ('state', 'not in', ['done', 'cancel'])
            ])
            
            _logger.info(f"Found {len(existing_pickings)} existing deliveries: {existing_pickings.mapped('name')}")
            
            if existing_pickings:
                cancelled_names = []
                for picking in existing_pickings:
                    if picking.state == 'assigned':
                        picking.do_unreserve()
                    picking.action_cancel()
                    cancelled_names.append(picking.name)
                    _logger.info(f"Cancelled delivery: {picking.name}")
                
                delivery_info.append(f"✅ Entregas canceladas: {', '.join(cancelled_names)}")
            
            # Step 2: Force new delivery creation using procurement
            _logger.info("=== RECREATING DELIVERIES ===")
            
            # Ensure procurement group exists
            if not order.procurement_group_id:
                group_vals = order._prepare_procurement_group()
                order.procurement_group_id = self.env['procurement.group'].create(group_vals)
            
            # Get the sale order line
            line = self.sale_order_line_id
            
            # Prepare procurement values with flexible BOM context
            procurement_values = line._prepare_procurement_values(order.procurement_group_id)
            procurement_values.update({
                'force_flexible_bom': True,
                'flexible_bom_id': line.flexible_bom_id.id if line.flexible_bom_id else False
            })
            
            # Create procurement with flexible BOM context
            procurement = self.env['procurement.group'].Procurement(
                line.product_id,
                line.product_uom_qty,
                line.product_uom,
                line.order_partner_shipping_id.property_stock_customer,
                line.name,
                order.name,
                line.company_id,
                procurement_values
            )
            
            # Run procurement with context
            self.env['procurement.group'].with_context(
                force_flexible_bom=True,
                flexible_bom_id=line.flexible_bom_id.id if line.flexible_bom_id else False
            ).run([procurement])
            
            _logger.info("Procurement run completed")
            
            # Step 3: Verify new deliveries were created
            self.env.cr.commit()  # Ensure changes are saved
            
            new_pickings = self.env['stock.picking'].search([
                ('origin', '=', order.name),
                ('state', 'not in', ['done', 'cancel'])
            ])
            
            if new_pickings:
                new_names = ', '.join(new_pickings.mapped('name'))
                delivery_info.append(f"✅ Nuevas entregas creadas: {new_names}")
                _logger.info(f"Successfully created new deliveries: {new_names}")
            else:
                # Try alternative method
                _logger.warning("No new deliveries found, trying alternative method")
                line._action_launch_stock_rule()
                
                # Check again
                final_pickings = self.env['stock.picking'].search([
                    ('origin', '=', order.name),
                    ('state', 'not in', ['done', 'cancel'])
                ])
                
                if final_pickings:
                    final_names = ', '.join(final_pickings.mapped('name'))
                    delivery_info.append(f"✅ Entregas creadas (método alternativo): {final_names}")
                    _logger.info(f"Created deliveries with alternative method: {final_names}")
                else:
                    delivery_info.append("ℹ️ Las entregas se crearán automáticamente según las reglas de stock")
            
        except Exception as e:
            error_msg = f"⚠️ Error en actualización de entregas: {str(e)}"
            delivery_info.append(error_msg)
            _logger.error(f"Error in delivery update: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
        
        result = '\n'.join(delivery_info)
        _logger.info(f"Delivery update completed. Result: {result}")
        return result

    def action_add_bom_line(self):
        """Add new BOM line"""
        return {
            'name': 'Add Component',
            'type': 'ir.actions.act_window',
            'res_model': 'flexible.bom.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_wizard_id': self.id,
            }
        }


class FlexibleBomLineWizard(models.TransientModel):
    _name = 'flexible.bom.line.wizard'
    _description = 'Flexible BOM Line Wizard'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'flexible.bom.wizard',
        string='Wizard'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Component',
        required=True
    )
    
    product_qty = fields.Float(
        string='Quantity',
        default=1.0,
        required=True
    )
    
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id


class FlexibleBomRoutingWizard(models.TransientModel):
    _name = 'flexible.bom.routing.wizard'
    _description = 'Flexible BOM Routing Wizard'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'flexible.bom.wizard',
        string='Wizard'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    name = fields.Char(
        string='Operation Name',
        required=True
    )
    
    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Work Center',
        required=True
    )
    
    time_cycle = fields.Float(
        string='Duration (minutes)',
        default=60.0,
        required=True
    )

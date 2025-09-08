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
    
    # Fields to track BOM creation status
    created_bom_id = fields.Many2one(
        'mrp.bom',
        string='Created BOM',
        help='The flexible BOM that was created'
    )
    
    creation_message = fields.Text(
        string='Creation Message',
        help='Message about the BOM creation process'
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

    def action_create_bom_and_delivery(self):
        """Create the flexible BOM and delivery in one step"""
        self.ensure_one()
        
        _logger.info(f"=== Starting BOM and delivery creation ===")
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
        
        # Store created BOM
        self.created_bom_id = new_bom.id
        
        # For confirmed orders, also create delivery
        if self.order_confirmed:
            # Cancel existing deliveries first
            if self.cancel_existing_deliveries:
                try:
                    delivery_message = self._cancel_existing_deliveries()
                    _logger.info(f"Delivery cancellation completed with message: {delivery_message}")
                except Exception as e:
                    error_msg = f"Error durante cancelación de entregas: {str(e)}"
                    _logger.error(error_msg)
            
            # Create new delivery
            try:
                result = self._create_delivery_with_flexible_bom()
                if result.get('success'):
                    success_msg = f'✅ BOM Flexible "{new_bom.code}" creada y nueva entrega generada exitosamente.'
                    if result.get('picking_name'):
                        success_msg += f'\n📦 Nueva entrega: {result["picking_name"]}'
                    
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'BOM y Entrega Creados',
                            'message': success_msg,
                            'type': 'success',
                            'sticky': True,
                        }
                    }
                else:
                    error_msg = f'BOM creada, pero error en entrega: {result.get("error", "Error desconocido")}'
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'BOM Creada - Error en Entrega',
                            'message': error_msg,
                            'type': 'warning',
                            'sticky': True,
                        }
                    }
            except Exception as e:
                error_msg = f'BOM creada, pero error en entrega: {str(e)}'
                _logger.error(error_msg)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'BOM Creada - Error en Entrega',
                        'message': error_msg,
                        'type': 'warning',
                        'sticky': True,
                    }
                }
        else:
            # For draft orders, update price automatically
            self._update_sale_line_price()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'BOM Creada',
                    'message': f'✅ BOM Flexible "{new_bom.code}" creada exitosamente.',
                    'type': 'success',
                }
            }

    def action_create_bom(self):
        """Legacy method - redirect to new combined action"""
        return self.action_create_bom_and_delivery()

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

    def _cancel_existing_deliveries(self):
        """Cancel existing deliveries for the sale order (separated from recreation)"""
        _logger.info(f"=== CANCELLING EXISTING DELIVERIES ===")
        _logger.info(f"Sale order line: {self.sale_order_line_id.id}")
        
        order = self.sale_order_line_id.order_id
        _logger.info(f"Processing sale order: {order.name}")
        
        delivery_info = []
        
        try:
            # Find all existing deliveries for this order
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
                delivery_info.append("ℹ️ Use el botón 'Crear Nuevo Delivery' para generar la entrega con la BOM personalizada")
            else:
                delivery_info.append("ℹ️ No se encontraron entregas para cancelar")
            
        except Exception as e:
            error_msg = f"⚠️ Error en cancelación de entregas: {str(e)}"
            delivery_info.append(error_msg)
            _logger.error(f"Error in delivery cancellation: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
        
        result = '\n'.join(delivery_info)
        _logger.info(f"Delivery cancellation completed. Result: {result}")
        return result

    def _create_delivery_with_flexible_bom(self):
        """Helper method to create delivery with flexible BOM - returns result dict"""
        _logger.info(f"=== CREATING DELIVERY WITH FLEXIBLE BOM ===")
        
        order = self.sale_order_line_id.order_id
        line = self.sale_order_line_id
        
        # Verify we have a flexible BOM
        if not line.flexible_bom_id:
            return {
                'success': False,
                'error': 'No flexible BOM found on sale order line'
            }
        
        try:
            # Method 1: Try using stock rule with flexible BOM context
            _logger.info("🔄 Method 1: Using _action_launch_stock_rule() with flexible BOM context")
            
            try:
                line_with_context = line.with_context(
                    force_flexible_bom=True,
                    flexible_bom_id=line.flexible_bom_id.id,
                    use_flexible_bom=True
                )
                
                line_with_context._action_launch_stock_rule()
                self.env.cr.commit()
                
                # Check if delivery was created
                new_pickings = self.env['stock.picking'].search([
                    ('origin', '=', order.name),
                    ('state', 'not in', ['done', 'cancel'])
                ])
                
                if new_pickings:
                    delivery_name = ', '.join(new_pickings.mapped('name'))
                    _logger.info(f"✅ Method 1 SUCCESS: Created deliveries: {delivery_name}")
                    return {
                        'success': True,
                        'picking_name': delivery_name,
                        'method': 'stock_rule'
                    }
                    
            except Exception as e1:
                _logger.error(f"❌ Method 1 failed: {str(e1)}")
            
            # Method 2: Manual creation if Method 1 failed
            _logger.info("🔄 Method 2: Manual delivery creation")
            
            flexible_bom = line.flexible_bom_id
            bom_lines = flexible_bom.bom_line_ids
            
            if bom_lines:
                # Create picking with proper sale order linkage
                picking_type = order.warehouse_id.out_type_id
                
                # Ensure procurement group exists and is linked
                if not order.procurement_group_id:
                    group_vals = order._prepare_procurement_group()
                    order.procurement_group_id = self.env['procurement.group'].create(group_vals)
                
                picking_vals = {
                    'picking_type_id': picking_type.id,
                    'partner_id': order.partner_shipping_id.id,
                    'origin': order.name,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': order.partner_shipping_id.property_stock_customer.id,
                    'company_id': order.company_id.id,
                    'state': 'draft',
                    'group_id': order.procurement_group_id.id,
                }
                
                # Try to add sale_id if the field exists
                try:
                    if 'sale_id' in self.env['stock.picking']._fields:
                        picking_vals['sale_id'] = order.id
                except Exception:
                    pass
                
                new_picking = self.env['stock.picking'].create(picking_vals)
                
                # Create moves for each component
                moves_created = 0
                for bom_line in bom_lines:
                    component_qty = bom_line.product_qty * line.product_uom_qty
                    
                    move_vals = {
                        'name': f"{line.name} - {bom_line.product_id.name}",
                        'product_id': bom_line.product_id.id,
                        'product_uom_qty': component_qty,
                        'product_uom': bom_line.product_uom_id.id,
                        'picking_id': new_picking.id,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': order.partner_shipping_id.property_stock_customer.id,
                        'sale_line_id': line.id,
                        'company_id': order.company_id.id,
                        'state': 'draft',
                        'procure_method': 'make_to_stock',
                        'group_id': order.procurement_group_id.id,
                        'origin': order.name,
                    }
                    
                    self.env['stock.move'].create(move_vals)
                    moves_created += 1
                
                if moves_created > 0:
                    new_picking.action_confirm()
                    _logger.info(f"✅ Method 2 SUCCESS: Created picking {new_picking.name} with {moves_created} moves")
                    return {
                        'success': True,
                        'picking_name': new_picking.name,
                        'method': 'manual'
                    }
            
            return {
                'success': False,
                'error': 'No BOM lines found or could not create delivery'
            }
            
        except Exception as e:
            _logger.error(f"Error in _create_delivery_with_flexible_bom: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def action_create_delivery(self):
        """Legacy method - creates delivery only (for backward compatibility)"""
        result = self._create_delivery_with_flexible_bom()
        
        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'title': 'Delivery Creado',
                    'message': f'Nueva entrega creada exitosamente: {result["picking_name"]}',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': 'Error',
                    'message': f'No se pudo crear la entrega: {result.get("error", "Error desconocido")}',
                    'sticky': False,
                }
            }

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
            
            # Step 2: Force new delivery creation using multiple methods
            _logger.info("=== RECREATING DELIVERIES ===")
            
            # Ensure procurement group exists
            if not order.procurement_group_id:
                group_vals = order._prepare_procurement_group()
                order.procurement_group_id = self.env['procurement.group'].create(group_vals)
            
            # Get the sale order line
            line = self.sale_order_line_id
            
            # CRITICAL: Verify the flexible BOM is properly linked
            if not line.flexible_bom_id:
                _logger.error("❌ CRITICAL: Sale order line does not have flexible_bom_id set!")
                delivery_info.append("⚠️ Error: La línea de venta no tiene BOM flexible asignada")
                return '\n'.join(delivery_info)
            else:
                _logger.info(f"✅ Sale line linked to flexible BOM: {line.flexible_bom_id.id}")
            
            # Method 1: Try using direct stock rule action with flexible BOM context
            _logger.info("🔄 Method 1: Using _action_launch_stock_rule() with flexible BOM context")
            
            try:
                # Set context to force flexible BOM usage
                line_with_context = line.with_context(
                    force_flexible_bom=True,
                    flexible_bom_id=line.flexible_bom_id.id,
                    use_flexible_bom=True
                )
                
                # Call the stock rule directly
                line_with_context._action_launch_stock_rule()
                _logger.info("Stock rule launched with flexible BOM context")
                
                # Check if deliveries were created
                self.env.cr.commit()  # Ensure changes are committed
                
                new_pickings_method1 = self.env['stock.picking'].search([
                    ('origin', '=', order.name),
                    ('state', 'not in', ['done', 'cancel'])
                ])
                
                if new_pickings_method1:
                    names = ', '.join(new_pickings_method1.mapped('name'))
                    delivery_info.append(f"✅ Entregas creadas: {names}")
                    _logger.info(f"✅ Method 1 SUCCESS: Created deliveries: {names}")
                    
                    # Log the components to verify flexible BOM usage
                    for picking in new_pickings_method1:
                        move_products = picking.move_ids.mapped('product_id.name')
                        _logger.info(f"📦 Delivery {picking.name} components: {move_products}")
                    
                    return '\n'.join(delivery_info)  # Success, exit early
                else:
                    _logger.warning("⚠️ Method 1 failed - no deliveries created")
                    
            except Exception as e1:
                _logger.error(f"❌ Method 1 error: {str(e1)}")
            
            # Method 2: Create delivery manually based on flexible BOM components
            _logger.info("🔄 Method 2: Manual delivery creation from flexible BOM")
            
            try:
                # Get BOM components directly from flexible BOM
                flexible_bom = line.flexible_bom_id
                bom_lines = flexible_bom.bom_line_ids
                _logger.info(f"📋 Flexible BOM has {len(bom_lines)} components: {[bl.product_id.name for bl in bom_lines]}")
                
                if bom_lines:
                    # Create a new picking manually
                    picking_type = order.warehouse_id.out_type_id
                    
                    new_picking = self.env['stock.picking'].create({
                        'picking_type_id': picking_type.id,
                        'partner_id': order.partner_shipping_id.id,
                        'origin': order.name,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': order.partner_shipping_id.property_stock_customer.id,
                        'company_id': order.company_id.id,
                        'state': 'draft',
                    })
                    _logger.info(f"📦 Created new picking: {new_picking.name}")
                    
                    # Create moves for each flexible BOM component
                    moves_created = 0
                    for bom_line in bom_lines:
                        component_qty = bom_line.product_qty * line.product_uom_qty
                        
                        move_vals = {
                            'name': f"{line.name} - {bom_line.product_id.name}",
                            'product_id': bom_line.product_id.id,
                            'product_uom_qty': component_qty,
                            'product_uom': bom_line.product_uom_id.id,
                            'picking_id': new_picking.id,
                            'location_id': picking_type.default_location_src_id.id,
                            'location_dest_id': order.partner_shipping_id.property_stock_customer.id,
                            'sale_line_id': line.id,
                            'company_id': order.company_id.id,
                            'state': 'draft',
                            'procure_method': 'make_to_stock',
                        }
                        
                        move = self.env['stock.move'].create(move_vals)
                        moves_created += 1
                        _logger.info(f"✅ Created move for {bom_line.product_id.name} qty: {component_qty}")
                    
                    # Confirm the picking to make it ready
                    if moves_created > 0:
                        new_picking.action_confirm()
                        delivery_info.append(f"✅ Entrega creada manualmente: {new_picking.name} ({moves_created} componentes)")
                        _logger.info(f"✅ Method 2 SUCCESS: Created picking {new_picking.name} with {moves_created} moves")
                        return '\n'.join(delivery_info)  # Success
                    else:
                        _logger.error("❌ No moves created for the picking")
                        new_picking.unlink()  # Remove empty picking
                else:
                    _logger.error("❌ No components found in flexible BOM")
                    
            except Exception as e2:
                _logger.error(f"❌ Method 2 error: {str(e2)}")
                import traceback
                _logger.error(traceback.format_exc())
            
            # If all methods failed
            delivery_info.append("⚠️ No se pudo recrear la entrega automáticamente")
            _logger.error("❌ All delivery recreation methods failed")
            
        except Exception as e:
            error_msg = f"⚠️ Error en actualización de entregas: {str(e)}"
            delivery_info.append(error_msg)
            _logger.error(f"Error in delivery update: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
        
        result = '\n'.join(delivery_info)
        _logger.info(f"Delivery update completed. Result: {result}")
        return result
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

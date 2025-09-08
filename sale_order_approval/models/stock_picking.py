# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_merge_duplicate_moves(self):
        """
        Merge duplicate stock moves by summing their quantities.
        This helps consolidate repeated products into single lines in delivery orders.
        """
        if not self.move_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sin movimientos',
                    'message': 'No hay movimientos para fusionar.',
                    'type': 'warning'
                }
            }
        
        # Only allow merging in draft, waiting, confirmed, or assigned states
        if self.state not in ['draft', 'waiting', 'confirmed', 'assigned']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Estado no válido',
                    'message': 'Solo se pueden fusionar movimientos en estado borrador, esperando, confirmado o asignado.',
                    'type': 'warning'
                }
            }
        
        # Group moves by product and locations
        move_groups = {}
        moves_to_remove = []
        
        for move in self.move_ids.filtered(lambda m: m.state not in ['done', 'cancel']):
            # Create a key that includes product, locations, and other relevant fields
            key = (
                move.product_id.id,
                move.location_id.id,
                move.location_dest_id.id,
                move.product_uom.id,
                move.sale_line_id.id if move.sale_line_id else None
            )
            
            if key in move_groups:
                # Add quantity to existing group
                move_groups[key]['total_qty'] += move.product_uom_qty
                move_groups[key]['moves_to_merge'].append(move)
                moves_to_remove.append(move)
            else:
                # Create new group
                move_groups[key] = {
                    'main_move': move,
                    'total_qty': move.product_uom_qty,
                    'moves_to_merge': []
                }
        
        # Count duplicates found
        duplicates_found = 0
        merged_moves = []
        
        # Update main moves with consolidated quantities and remove duplicates
        for group_data in move_groups.values():
            if group_data['moves_to_merge']:  # Has duplicates
                main_move = group_data['main_move']
                old_qty = main_move.product_uom_qty
                new_qty = group_data['total_qty']
                
                # Update the main move with total quantity
                main_move.product_uom_qty = new_qty
                
                # If the move was already reserved, we need to update reservations
                if main_move.state == 'assigned':
                    # Cancel current reservations
                    main_move._do_unreserve()
                    # The picking will need to be re-assigned to get new reservations
                
                duplicates_found += len(group_data['moves_to_merge'])
                merged_moves.append(f"{main_move.product_id.display_name}: {old_qty} → {new_qty}")
                
                _logger.info(f"Merged {main_move.product_id.display_name}: {old_qty} + {len(group_data['moves_to_merge'])} duplicates = {new_qty}")
        
        # Remove duplicate moves
        if moves_to_remove:
            for move in moves_to_remove:
                move.unlink()
        
        # Re-assign the picking if it was partially assigned
        if self.state == 'assigned' and duplicates_found > 0:
            try:
                self.action_assign()
            except Exception as e:
                _logger.warning(f"Could not re-assign picking after merging: {e}")
        
        # Show result notification
        if duplicates_found > 0:
            message = f"✅ Se fusionaron {duplicates_found} movimientos duplicados:\n" + "\n".join(merged_moves)
            notification_type = 'success'
            title = 'Movimientos Fusionados'
        else:
            message = "ℹ️ No se encontraron movimientos duplicados para fusionar."
            notification_type = 'info'
            title = 'Sin duplicados'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': True if duplicates_found > 0 else False
            }
        }

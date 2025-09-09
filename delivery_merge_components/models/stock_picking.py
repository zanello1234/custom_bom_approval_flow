# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import defaultdict


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_merge_duplicate_moves(self):
        """
        Merge duplicate stock moves in a delivery order.
        Groups moves by product, location, UOM, and sale line, then consolidates quantities.
        """
        if not self.move_ids_without_package:
            raise UserError(_("No hay movimientos para fusionar."))

        # Group moves by key (product, location_src, location_dest, product_uom, sale_line_id)
        move_groups = defaultdict(list)
        
        for move in self.move_ids_without_package:
            # Create grouping key
            key = (
                move.product_id.id,
                move.location_id.id,
                move.location_dest_id.id,
                move.product_uom.id,
                move.sale_line_id.id if move.sale_line_id else False
            )
            move_groups[key].append(move)
        
        merged_count = 0
        
        # Process each group
        for key, moves in move_groups.items():
            if len(moves) > 1:  # Only process groups with duplicates
                # Keep the first move as the main one
                main_move = moves[0]
                duplicate_moves = moves[1:]
                
                # Sum all quantities
                total_quantity = sum(move.product_uom_qty for move in moves)
                
                # Update main move with total quantity
                main_move.write({
                    'product_uom_qty': total_quantity,
                })
                
                # Handle stock reservations if any
                total_reserved = sum(move.reserved_availability for move in moves)
                if total_reserved > 0:
                    main_move.write({
                        'reserved_availability': total_reserved,
                    })
                
                # Delete duplicate moves
                for dup_move in duplicate_moves:
                    # Cancel the move first if it's not done
                    if dup_move.state not in ('done', 'cancel'):
                        dup_move._action_cancel()
                    dup_move.unlink()
                
                merged_count += len(duplicate_moves)
        
        if merged_count > 0:
            message = _("Se fusionaron %d movimientos duplicados.") % merged_count
            self.message_post(body=message)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Fusión Completada"),
                    'message': message,
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Sin Duplicados"),
                    'message': _("No se encontraron movimientos duplicados para fusionar."),
                    'type': 'info',
                }
            }

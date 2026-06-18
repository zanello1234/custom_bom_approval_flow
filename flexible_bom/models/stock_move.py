# -*- coding: utf-8 -*-

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _compute_kit_quantities(self, product_id, kit_qty, kit_bom, filters):
        """Tolerate sale order lines whose moves accumulated several flexible
        phantom BOMs for the same product.

        Core Odoo (sale_mrp._compute_qty_delivered) assumes a single phantom
        BOM per kit line and calls ``kit_bom.product_qty``, which raises
        ``Expected singleton: mrp.bom(322, 328)`` when more than one matches.
        Older data created by the flexible-BOM wizard (one new BOM per
        customization) can leave such lines. We defensively keep a single BOM
        so the quantity can still be computed instead of crashing the whole
        recompute. New customizations no longer accumulate BOMs (the wizard now
        reuses one BOM per line), so this only protects legacy records.
        """
        if hasattr(kit_bom, '__len__') and len(kit_bom) > 1:
            _logger.warning(
                "Multiple kit BOMs for %s in _compute_kit_quantities: %s. "
                "Using the first to avoid a singleton error.",
                product_id.display_name, kit_bom.ids,
            )
            kit_bom = kit_bom[:1]
        return super()._compute_kit_quantities(product_id, kit_qty, kit_bom, filters)

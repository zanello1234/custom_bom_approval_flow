# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.model
    def _bom_find(self, products=None, **kwargs):
        """Override BOM search to prioritize flexible BOMs in sale order context.

        IMPORTANT: Odoo 18's _bom_find contract returns a
        `defaultdict(lambda: self.env['mrp.bom'])` mapping each product to its
        BoM (or an empty recordset when none matches). Returning a plain
        recordset breaks every internal caller — they index the result as
        `result[product]`, which raises:

            TypeError: tuple indices must be integers or slices,
                       not product.product

        when the recordset's __getitem__ tries to interpret a product as an
        integer index. That used to be the source of the "Method 1 failed"
        fallback in the flexible_bom_wizard logs.
        """
        # Handle both old and new method signatures for backward compatibility
        product_tmpl = kwargs.get('product_tmpl')
        product = kwargs.get('product')

        # If products parameter is provided (new signature), extract product
        # from it for the flexible-BOM matching check below.
        if products and not product and not product_tmpl:
            if hasattr(products, '__iter__'):
                product = products[0] if products else None
            else:
                product = products

        # Normalize products to something iterable for the dict mapping
        if products is not None:
            products_iter = products
        elif product:
            products_iter = product
        else:
            products_iter = self.env['product.product']

        flexible_bom_id = self.env.context.get('flexible_bom_id')
        sale_line_id = self.env.context.get('sale_line_id')

        if flexible_bom_id:
            flexible_bom = self.browse(flexible_bom_id)
            if flexible_bom.exists():
                _logger.info(
                    "🎯 Using flexible BOM from context: %s",
                    flexible_bom.display_name,
                )
                return self._build_flexible_bom_result(
                    products_iter, flexible_bom,
                )

        if sale_line_id:
            sale_line = self.env['sale.order.line'].browse(sale_line_id)
            if sale_line.exists() and hasattr(sale_line, 'flexible_bom_id') \
                    and sale_line.flexible_bom_id:
                flexible_bom = sale_line.flexible_bom_id
                # Only apply when the flexible BOM actually matches the
                # product/template being looked up.
                product_match = product and flexible_bom.product_id == product
                tmpl_match = (
                    product_tmpl
                    and flexible_bom.product_tmpl_id == product_tmpl
                )
                if product_match or tmpl_match:
                    _logger.info(
                        "🎯 Using flexible BOM from sale line: %s",
                        flexible_bom.display_name,
                    )
                    return self._build_flexible_bom_result(
                        products_iter, flexible_bom,
                    )

        # If no flexible BOM context, delegate to standard logic
        try:
            if products is not None:
                # New signature with products parameter
                return super()._bom_find(
                    products,
                    **{k: v for k, v in kwargs.items()
                       if k not in ['product_tmpl', 'product']},
                )
            else:
                # Old signature - reconstruct products from individual params
                if product:
                    return super()._bom_find(
                        product,
                        **{k: v for k, v in kwargs.items()
                           if k not in ['product_tmpl', 'product']},
                    )
                elif product_tmpl:
                    products_for_tmpl = self.env['product.product'].search(
                        [('product_tmpl_id', '=', product_tmpl.id)],
                    )
                    if products_for_tmpl:
                        return super()._bom_find(
                            products_for_tmpl,
                            **{k: v for k, v in kwargs.items()
                               if k not in ['product_tmpl', 'product']},
                        )
                    return super()._bom_find(
                        self.env['product.product'],
                        **{k: v for k, v in kwargs.items()
                           if k not in ['product_tmpl', 'product']},
                    )
                else:
                    # No products specified, return empty mapping
                    return defaultdict(lambda: self.env['mrp.bom'])
        except TypeError:
            # Fallback for unexpected old-style calls
            return super()._bom_find(**kwargs)

    def _build_flexible_bom_result(self, products_iter, flexible_bom):
        """Build the dict-shaped response expected by Odoo 18 callers.

        Always returns a defaultdict so that callers indexing with an
        unknown product receive an empty mrp.bom recordset rather than
        a KeyError.

        IMPORTANT: the flexible BOM must only be returned for the product it
        actually belongs to. Mapping it to *every* product makes mrp.bom
        ``explode()`` treat each kit component as the same phantom kit, which
        recurses into itself indefinitely until the worker hits the 900s time
        limit and Odoo reloads it. We therefore match by variant
        (``product_id``) or, for template-level BOMs, by template
        (``product_tmpl_id``); any other product keeps the empty recordset
        provided by the defaultdict.
        """
        result = defaultdict(lambda: self.env['mrp.bom'])
        if products_iter is None:
            return result
        # products_iter can be a recordset or a single record
        iterable = products_iter if hasattr(products_iter, '__iter__') \
            else [products_iter]
        for prod in iterable:
            if flexible_bom.product_id:
                # BOM tied to a specific variant: only that variant matches.
                if prod == flexible_bom.product_id:
                    result[prod] = flexible_bom
            elif prod.product_tmpl_id == flexible_bom.product_tmpl_id:
                # Template-level BOM: match any variant of the same template.
                result[prod] = flexible_bom
            # else: leave the empty recordset -> stops the explode() recursion
        return result

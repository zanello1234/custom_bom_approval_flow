# -*- coding: utf-8 -*-
"""Post-migration placeholder for flexible_bom 18.0.1.2.3.

This version only bumps the manifest to trigger an upgrade for the
"force delivery cancellation when active pickings exist" fix in the
wizard. No data migration is required — the change is purely in
Python/XML and adds a new computed field that resolves on demand.
"""


def migrate(cr, version):
    # Intentionally no-op: the upgrade carries no schema or data changes.
    return

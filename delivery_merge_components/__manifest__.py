{
    'name': 'Delivery Merge Components',
    'version': '18.0.1.0.0',
    'summary': '🔄 Merge duplicate components in delivery orders',
    'description': """
Delivery Merge Components
=========================

Adds functionality to merge duplicate product components in delivery orders.

🎯 **Key Features:**
• **Merge Button**: Easy-to-use button in delivery order operations
• **Smart Grouping**: Groups identical products by location and UOM
• **Quantity Consolidation**: Automatically sums quantities of duplicate items
• **Reservation Handling**: Properly manages stock reservations during merge
• **Clean Interface**: Intuitive button placement in operations section

📋 **How it Works:**
1. **Identify Duplicates**: Finds products with same product, location, UOM, and sale line
2. **Consolidate**: Merges duplicate lines into single line with total quantity
3. **Clean Up**: Removes empty duplicate lines automatically
4. **Preserve Data**: Maintains all important information (locations, reservations, etc.)

💼 **Business Benefits:**
• Cleaner delivery orders with consolidated product lines
• Reduced confusion for warehouse staff
• Better inventory management and picking efficiency
• Simplified delivery documentation

🔧 **Technical Features:**
• Extends stock.picking model with merge functionality
• Safe consolidation that preserves stock moves integrity
• User-friendly button in delivery order form view
• Compatible with standard Odoo inventory workflows
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'category': 'Inventory/Inventory',
    'depends': ['stock'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

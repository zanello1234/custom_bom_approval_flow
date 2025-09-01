{
    'name': 'Sale Order Approval Workflow',
    'version': '18.0.1.2.1',
    'summary': '✅ Add Approval state to Sale Orders - Required step before confirmation',
    'description': """
Sale Order Approval Workflow
============================

Adds an "Approved" state to Sale Orders requiring approval before confirmation.

🎯 **Key Features:**
• **Approved State**: New state that requires explicit approval
• **Approval Button**: "Approve" button to move orders to approved state
• **Controlled Confirmation**: Confirm button only available after approval
• **Clear Workflow**: Better control over order processing

📋 **Enhanced Workflow:**
1. **Draft/Sent** → *Approve* → **Approved** 
2. **Approved** → *Customize BOM* → **BOM Customization**
3. **BOM Customization** → *Confirm* → **Sale Order** (creates deliveries/MOs)

💼 **Business Benefits:**
• Mandatory approval step for all sales orders
• Integrated BOM customization phase for flexible manufacturing
• Better control over order processing authorization
• Clear separation between sales, approval, and customization processes
• Improved compliance and oversight

🔧 **Technical Features:**
• Simple state extension without complex inheritance
• Minimal changes to existing workflow
• Compatible with standard Odoo sales functionality
• Integrated with Flexible BOM module for advanced manufacturing workflows
• Clean and maintainable code structure
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'category': 'Sales',
    'depends': ['sale'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

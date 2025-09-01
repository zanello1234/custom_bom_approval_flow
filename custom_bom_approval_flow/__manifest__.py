{
    'name': 'Custom BOM Approval Flow',
    'version': '18.0.1.0.0',
    'summary': '🏢 Complete Sale Order Management Solution - Approval Workflow + Flexible BOM Configuration',
    'description': """
Custom BOM Approval Flow
========================

Complete business solution that combines approval workflow and flexible BOM management for advanced sale order processing.

🎯 **What is Custom BOM Approval Flow?**
A comprehensive APP that automatically installs and integrates our complete sale order management suite, providing a unified business solution for companies requiring both approval control and flexible manufacturing setup.

📦 **Included Modules:**
• **Sale Order Approval Workflow** - Multi-stage approval system with Spanish localization
• **Flexible BOM Configuration** - Dynamic BOM creation from sales orders

🏭 **Complete Workflow:**
1. **Draft/Sent** → *Approve* → **Approved** 
2. **Approved** → *Customize BOM* → **BOM Customization**
3. **BOM Customization** → *Confirm* → **Sale Order** (creates deliveries/MOs)

💼 **Business Benefits:**
• **One-Click Installation** - Get the complete solution instantly
• **Integrated Workflow** - Seamless transition between approval and BOM customization
• **Spanish Localization** - All messages and interfaces in Spanish
• **Professional Control** - Mandatory approval + flexible manufacturing setup
• **Scalable Architecture** - Modular design allows individual module updates

🔧 **Perfect For:**
• Manufacturing companies requiring approval workflows
• Make-to-order businesses with configurable products
• Companies needing both sales control and production flexibility
• Organizations requiring Spanish-language interfaces

⚡ **Key Features:**
• **Zero Configuration** - Works out of the box
• **Progressive Workflow** - Guided step-by-step process
• **Button Control** - Smart UI that shows only relevant actions
• **Dependency Management** - Automatic module coordination
• **Update Safe** - Individual modules can be updated independently

🏗️ **Architecture:**
This is a meta-module that provides easy installation and management of the complete custom BOM approval workflow while maintaining clean separation of concerns.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'category': 'Sales/Management',
    'depends': [
        'sale_order_approval',
        'flexible_bom',
    ],
    'data': [],
    'demo': [],
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,  # Es una APP principal
    'sequence': 5,        # Alta prioridad en el listado
    'license': 'LGPL-3',
    'price': 0.00,
    'currency': 'USD',
    'live_test_url': '',
    'support': 'support@yourcompany.com',
    'maintainer': 'Your Company Development Team',
}

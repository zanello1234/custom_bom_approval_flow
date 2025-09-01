{
    'name': 'Flexible BOM - Custom Manufacturing & Kits',
    'version': '18.0.1.2.2',
    'summary': '🔧 Create custom BOMs from sales orders | Manufacturing & Kit BOMs | Interactive wizard configuration',
    'description': """
Flexible BOM - Custom Manufacturing & Kit Configuration
======================================================

Transform your make-to-order business with dynamic BOM creation directly from sales orders!

🎯 **Key Features:**
• **Interactive Wizard**: Configure custom BOMs with an intuitive interface
• **Manufacturing & Kit BOMs**: Support for both production and kit scenarios
• **Real-time Pricing**: Automatic price calculation based on selected components
• **Sales Integration**: Seamless integration with Odoo sales workflow & approval process
• **Component Flexibility**: Add, remove, or modify components per order
• **Production Ready**: Automatic manufacturing order creation with custom BOMs
• **Approval Workflow**: Integrated with sale order approval for controlled BOM customization

🏭 **Perfect For:**
• Printing companies (custom posters, business cards)
• Furniture manufacturers (configurable materials & finishes)
• Electronics assembly (custom computer builds)
• Gift & package companies (variable product bundles)
• Any make-to-order business requiring flexible configurations

💼 **Business Benefits:**
• Reduce quote preparation time by 80%
• Eliminate BOM maintenance overhead
• Increase sales flexibility and customer satisfaction
• Streamline custom product manufacturing
• Maintain full traceability from quote to production

🔧 **How It Works:**
1. Create sales order and approve it
2. Mark products as "Flexible BOM"
3. Configure custom BOMs during BOM customization phase
4. Choose between Manufacturing or Kit BOMs
5. Confirm order for automatic production with custom specifications

📊 **Reporting & Tracking:**
• Full traceability from sales order to production
• Custom BOM cost analysis
• Component usage tracking
• Manufacturing efficiency metrics

🚀 **Odoo 18 Ready:**
• Fully compatible with latest Odoo version
• Modern UI/UX design
• Mobile-friendly interface
• Multi-company support

Transform your business today with Flexible BOM!
    """,
    'category': 'Manufacturing',
    'author': 'Odoo Experts',
    'website': 'https://www.odoo-experts.com',
    'license': 'LGPL-3',
    'price': 99.00,
    'currency': 'USD',
    'images': [
        'static/description/banner.png',
        'static/description/main_screenshot.png',
        'static/description/wizard_screenshot.png',
        'static/description/bom_configuration.png',
    ],
    'depends': [
        'base',
        'sale',
        'mrp',
        'product',
        'stock',
        'sale_order_approval',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cleanup_data.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'wizard/flexible_bom_wizard_views.xml',
        'wizard/base_bom_setup_wizard_views.xml',
        'views/mrp_bom_views.xml',
        'views/base_bom_actions.xml',
    ],
    'demo': [],
    'qweb': [],
    'external_dependencies': {
        'python': [],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 20,
    'live_test_url': 'https://demo.odoo-experts.com/flexible-bom',
    'support': 'support@odoo-experts.com',
    'maintainer': 'Odoo Experts Team',
    'contributors': [
        'Development Team <dev@odoo-experts.com>',
    ],
}

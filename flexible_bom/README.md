# 🔧 Flexible BOM - Custom Manufacturing & Kit Configuration

[![Odoo 18](https://img.shields.io/badge/Odoo-18.0-blue.svg)](https://www.odoo.com)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Maintenance](https://img.shields.io/badge/Maintained-Yes-green.svg)](https://github.com/yourusername/flexible_bom)

> **Transform your make-to-order business with dynamic BOM creation directly from sales orders!**

## 🎯 Overview

Flexible BOM is a powerful Odoo 18 module that revolutionizes how businesses handle custom manufacturing and product kits. Instead of maintaining hundreds of predefined BOMs, create them dynamically during the sales process with an intuitive wizard interface.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🧙 **Interactive Wizard** | Configure custom BOMs with drag-and-drop simplicity |
| ⚙️ **Manufacturing & Kit BOMs** | Support for both production and kit scenarios |
| 💰 **Real-time Pricing** | Automatic cost calculation with configurable margins |
| 🔄 **Sales Integration** | Seamless workflow from quote to production |
| 📊 **Full Traceability** | Track from sales order to finished product |
| 🌐 **Multi-company** | Enterprise-ready with multi-company support |

## 🏭 Perfect For These Industries

### 🖨️ **Printing Companies**
- Custom posters with variable paper types
- Business cards with different finishes
- Marketing materials with client-specific requirements

### 🪑 **Furniture Manufacturers** 
- Tables with custom wood types and finishes
- Chairs with fabric/leather options
- Cabinets with variable hardware

### 💻 **Electronics Assembly**
- Custom computer builds
- Control panels with specific components
- Electronic devices with configurable specs

### 🎁 **Gift & Package Companies**
- Custom gift boxes with variable contents
- Promotional packages for events
- Product bundles with seasonal items

## 🚀 Quick Start Guide

### Installation

1. **Download** the module files
2. **Copy** to your Odoo addons directory:
   ```bash
   cp -r flexible_bom /path/to/odoo/addons/
   ```
3. **Update** apps list in Odoo
4. **Install** "Flexible BOM" module
5. **Configure** your first flexible product!

### Basic Configuration

#### Step 1: Enable Flexible BOM on Products
```
Manufacturing → Products → Products
→ Select/Create Product
→ Enable "Flexible BOM" checkbox
```

#### Step 2: Create Base BOM Template
```
Manufacturing → Bill of Materials
→ Create new BOM for your flexible product
→ Add standard components and operations
```

#### Step 3: Use in Sales Orders
```
Sales → Sales Orders → Create
→ Add flexible product to order line
→ Click "Configure BOM" button
→ Customize components and type
→ Save and continue with sales process
```

## 📖 Detailed Workflow

### 1. Product Setup
```python
# Mark product as flexible
product.is_flexible_bom = True
```

### 2. BOM Configuration Wizard
- **Components Tab**: Add, remove, or modify components
- **Operations Tab**: Configure work centers and timing (Manufacturing BOMs only)
- **BOM Type Selection**: Choose between Manufacturing or Kit

### 3. BOM Types

#### 🏭 Manufacturing BOM (`normal`)
- Requires production operations
- Creates manufacturing orders
- Full work center scheduling
- Quality control integration

#### 📦 Kit BOM (`phantom`)
- No manufacturing required
- Components delivered separately
- Faster order fulfillment
- Perfect for product bundles

### 4. Automatic Processes
- **Price Calculation**: Based on component costs + margin
- **BOM Creation**: Quote-specific BOM generation
- **Production Integration**: Seamless MO creation
- **Inventory Management**: Automatic stock reservations

## 🔧 Technical Details

### Dependencies
```python
'depends': [
    'base',           # Core Odoo functionality
    'sale',           # Sales order integration
    'mrp',            # Manufacturing features
    'product',        # Product management
    'stock',          # Inventory management
]
```

### Models Extended
- `product.template` - Flexible BOM field
- `sale.order.line` - BOM configuration integration
- `mrp.bom` - Flexible BOM tracking

### New Models
- `flexible.bom.wizard` - Main configuration interface
- `flexible.bom.line.wizard` - Component configuration
- `flexible.bom.routing.wizard` - Operations setup

### Security & Permissions
- User-level access for sales teams
- Manager-level for BOM modifications
- Multi-company isolation

## 📊 Advanced Features

### 🎯 Base BOM Management System
Prevents multiple manufacturing orders with intelligent BOM hierarchy:

```python
# Automatic base BOM identification
base_bom = self._find_base_bom_for_product(product_tmpl_id)
if base_bom:
    bom.base_bom_id = base_bom.id
    base_bom.is_base_bom = True
```

**Key Benefits:**
- ✅ **Single Source of Truth**: One base BOM per product for manufacturing
- ✅ **Automatic Detection**: System identifies base BOMs automatically  
- ✅ **Manufacturing Priority**: Base BOMs used for production orders
- ✅ **Flexible Derivation**: Multiple custom BOMs can derive from one base
- ✅ **Visual Management**: Clear BOM hierarchy in interface

**BOM Types:**
- 🔧 **Base BOM**: Template for manufacturing orders
- ⚙️ **Flexible BOM**: Customer-specific derived from base
- 📋 **Standard BOM**: Regular Odoo BOMs (unchanged)

### Price Calculation Logic
```python
def calculate_price(components, margin=1.2):
    total_cost = sum(component.cost * component.qty for component in components)
    return total_cost * margin
```

### Custom BOM Naming
```python
code = f"{sale_order.name}: {product.name} ({'Kit' if bom_type == 'phantom' else 'Manufacturing'})"
```

### Traceability Chain
```
Sales Order → Custom BOM → Manufacturing Order → Finished Product
     ↓              ↓              ↓                    ↓
  Quote Line   Component List   Work Orders       Delivery
```

## 🔄 Business Process Integration

### Sales Process
1. **Quote Creation** → Add flexible products
2. **BOM Configuration** → Customize per customer needs
3. **Price Approval** → Automatic calculation
4. **Order Confirmation** → Generate production orders

### Manufacturing Process
1. **MO Creation** → Uses custom BOM automatically
2. **Component Planning** → MRP considers custom requirements
3. **Production Scheduling** → Work centers allocated
4. **Quality Control** → Standard QC procedures apply

### Inventory Impact
- **Component Reservations** → Automatic for custom BOMs
- **Forecasting** → MRP includes flexible products
- **Cost Tracking** → Real component costs captured

## 🛠️ Customization Options

### Configuration Parameters
```python
# Default margin for price calculation
ir.config_parameter: 'flexible_bom.default_margin' = '1.2'

# Enable/disable automatic price updates
ir.config_parameter: 'flexible_bom.auto_price_update' = 'True'
```

### Wizard Customization
- Add custom fields to wizard
- Implement business-specific validation
- Create custom component templates

### Reporting Extensions
- Custom BOM analysis reports
- Component usage statistics
- Margin analysis by product line

## 🔍 Troubleshooting

### Common Issues

#### BOM Not Creating
```
Check: Product has "Flexible BOM" enabled
Check: Base BOM exists for product
Check: User has proper permissions
```

#### Price Not Updating
```
Check: Components have cost prices set
Check: Margin configuration
Check: Price calculation method
```

#### Manufacturing Orders Missing Custom BOM
```
Check: Custom BOM created successfully
Check: Sales order confirmation process
Check: MRP settings for custom BOMs
```

## 📈 Performance Considerations

### Optimization Tips
- **Index custom BOM fields** for better search performance
- **Archive old custom BOMs** to maintain database speed
- **Use appropriate server resources** for wizard calculations

### Scalability
- Tested with **1000+ flexible products**
- Supports **concurrent wizard sessions**
- **Database cleanup** utilities included

## 🤝 Support & Contribution

### Getting Help
- 📧 **Email Support**: support@odoo-experts.com
- 💬 **Community Forum**: [Discuss.odoo.com](https://discuss.odoo.com)
- 📖 **Documentation**: [Wiki](https://github.com/yourusername/flexible_bom/wiki)

### Contributing
1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### Reporting Issues
Please use the [GitHub Issues](https://github.com/yourusername/flexible_bom/issues) tracker for:
- 🐛 Bug reports
- 💡 Feature requests
- 📝 Documentation improvements

## 📄 License

This project is licensed under the **LGPL-3.0 License** - see the [LICENSE](LICENSE) file for details.

## 🌟 Acknowledgments

- **Odoo Community** for the amazing platform
- **Beta Testers** who provided valuable feedback
- **Contributors** who helped improve the module

---

**Ready to revolutionize your manufacturing process?** 

🚀 [**Install Flexible BOM Today!**](https://apps.odoo.com/apps/modules/18.0/flexible_bom/)

---

*Made with ❤️ for the Odoo Community*

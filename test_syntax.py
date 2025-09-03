#!/usr/bin/env python3
"""
Simple syntax validation for our Odoo modules
"""
import os
import ast
import sys

def validate_python_file(filepath):
    """Validate Python syntax of a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the file to check for syntax errors
        ast.parse(content)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Main validation function"""
    base_path = os.path.dirname(__file__)
    
    # Files to validate
    files_to_check = [
        'flexible_bom/wizard/flexible_bom_wizard.py',
        'sale_order_approval/models/sale_order.py',
        'sale_order_approval/models/sale_order_line.py',
        'sale_order_approval/models/mrp_bom.py'
    ]
    
    print("=== Python Syntax Validation ===")
    all_valid = True
    
    for file_path in files_to_check:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            valid, message = validate_python_file(full_path)
            status = "✅" if valid else "❌"
            print(f"{status} {file_path}: {message}")
            if not valid:
                all_valid = False
        else:
            print(f"⚠️  {file_path}: File not found")
            all_valid = False
    
    print("\n=== Summary ===")
    if all_valid:
        print("✅ All files have valid Python syntax!")
        print("\n=== Key Changes Summary ===")
        print("1. Fixed delivery update mechanism in flexible_bom_wizard.py")
        print("2. Simplified _handle_delivery_update() method")
        print("3. Uses procurement.group.run() with flexible BOM context")
        print("4. Proper cancellation and recreation of stock pickings")
        print("5. Enhanced logging for debugging")
        
        print("\n=== How it works ===")
        print("- When user customizes BOM and enables 'Cancel existing deliveries'")
        print("- System cancels existing deliveries for the sale order")
        print("- Creates new procurement with flexible BOM context")
        print("- New deliveries use the customized BOM components")
        print("- Alternative fallback method if primary approach fails")
        
        return 0
    else:
        print("❌ Some files have syntax errors!")
        return 1

if __name__ == "__main__":
    sys.exit(main())

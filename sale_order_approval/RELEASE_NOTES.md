# Sale Order Approval - Release Notes

## Version 18.0.1.1.0

### New Features
- **BOM Customization State**: Added new workflow state "Customizar BOM" after approval
- **Progressive Workflow**: Complete 4-state workflow: Draft/Sent → Approved → BOM Customization → Sale
- **New Menu Items**: Added dedicated menu items for approved orders and BOM customization orders
- **Enhanced UI Controls**: Button visibility now follows the progressive workflow

### Workflow Changes
- Orders must now go through BOM customization phase before confirmation
- Added "Customize BOM" button (orange) visible only in approved state
- Confirm button now only appears in BOM customization state
- Updated state decorations in list and kanban views

### UI Improvements
- Context-aware banners guide users through the workflow process
- Color-coded states: Draft/Sent (blue), Approved (green), BOM Customization (orange), Sale (bold)
- Progressive button visibility ensures proper workflow sequence

### Technical Details
- Added `action_customize_bom()` method for state transition
- Enhanced `action_confirm()` with validation to require BOM customization
- Updated cancellation handling for new workflow states
- Improved chatter messages for better audit trail

## Version 18.0.1.0.1

### Initial Features
- **Approval Workflow**: Added "Approved" state to sale orders
- **Approve Button**: New button to approve quotations
- **UI Extensions**: Modified form, list, and kanban views
- **Access Control**: Basic approval workflow implementation

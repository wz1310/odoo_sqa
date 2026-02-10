# Report Builder Module for Odoo 18

A comprehensive report building tool that allows users to create custom reports with drag and drop functionality using modern OWL framework.

## Features

### 🎯 Core Functionality
- **Dynamic Model Selection**: Choose from any available Odoo model
- **Drag & Drop Interface**: Intuitive field selection with drag and drop
- **Real-time Preview**: See your report data before finalizing
- **Excel Export**: Export reports to Excel with formatting
- **Field Configuration**: Customize column labels, widths, alignment, and aggregation

### 🛠️ Technical Features
- **OWL Framework**: Built with Odoo 18's modern JavaScript framework
- **Responsive Design**: Works on desktop and mobile devices
- **Security Groups**: Proper access control with user and manager roles
- **Multi-company Support**: Respects company-specific data access
- **Performance Optimized**: Efficient data loading with pagination

### 📊 Report Management
- **Report Library**: Save and manage multiple reports
- **Report Sharing**: Share reports with team members
- **Report Templates**: Create reusable report templates
- **Automated Cleanup**: Automatic cleanup of temporary reports

## Installation

1. Copy the module to your Odoo addons directory
2. Update the app list in Odoo
3. Install the "Report Builder" module
4. Configure user permissions in Settings > Users & Companies > Groups

## Usage

### Creating a New Report

1. **Access Report Builder**
   - Go to Report Builder > Reports > Create Report
   - Or use Report Builder > Report Lab > Open Builder

2. **Select Model**
   - Choose the primary data model for your report
   - Models include Partners, Products, Sales Orders, etc.

3. **Select Fields**
   - Drag fields from the available list to the selected fields area
   - Or click on fields to add them
   - Reorder fields by dragging or using arrow buttons

4. **Configure Fields**
   - Set custom column labels
   - Adjust column widths
   - Choose alignment (left/center/right)
   - Set aggregation functions (sum, average, count, etc.)

5. **Preview & Export**
   - Preview your report data
   - Export to Excel format
   - Save the report for future use

### Managing Reports

- **My Reports**: View and manage your personal reports
- **All Reports**: (Managers only) View all reports in the system
- **Report Actions**: Edit, duplicate, archive, or delete reports

## Security & Permissions

### User Groups

- **Report Builder User**: Can create and manage own reports
- **Report Builder Manager**: Can manage all reports and system configuration

### Access Rules

- Users can only see their own reports by default
- Managers can access all reports
- Company-specific data access is enforced
- Multi-company environments are supported

## Technical Architecture

### Models

- `report.builder`: Main report configuration
- `report.builder.field`: Field configuration for reports
- `report.builder.related.field`: Related field configurations

### Controllers

- `/ubx_report_builder/models`: Get available models
- `/ubx_report_builder/model_fields`: Get fields for a model
- `/ubx_report_builder/save_report`: Save report configuration
- `/ubx_report_builder/preview_data`: Get preview data
- `/ubx_report_builder/export_excel`: Export to Excel

### Frontend Components

- **ReportBuilderWidget**: Main OWL component for the builder interface
- **FieldSelector**: Component for field selection with search and filtering
- **DragDropBuilder**: Drag and drop functionality for field ordering
- **ReportPreview**: Preview component with sorting and formatting

## Customization

### Adding Custom Field Types

To support custom field types, extend the field type mappings in:
- `getFieldIcon()` method for icons
- `getDefaultAlignment()` method for default alignment
- `getDefaultAggregation()` method for default aggregation

### Custom Export Formats

Extend the `action_export_excel()` method in the `report.builder` model to add support for additional export formats.

### Advanced Filtering

The module supports domain filters. You can add custom filter builders by extending the configuration step in the OWL components.

## Performance Considerations

- **Record Limits**: Default maximum of 1,000 records per report (configurable up to 10,000)
- **Data Caching**: Temporary reports are cached for performance
- **Automatic Cleanup**: Temporary reports are cleaned up daily
- **Pagination**: Preview uses pagination to avoid loading large datasets

## Configuration Parameters

- `ubx_report_builder.max_records_limit`: Maximum records per report (default: 10,000)
- `ubx_report_builder.auto_refresh_interval`: Auto-refresh interval in seconds (default: 300)
- `ubx_report_builder.enable_data_cache`: Enable data caching (default: True)

## Troubleshooting

### Common Issues

1. **No fields visible**: Ensure the selected model has accessible fields
2. **Export fails**: Check user permissions and file system access
3. **Performance issues**: Reduce max_records or add domain filters
4. **JavaScript errors**: Clear browser cache and check console for errors

### Debug Mode

Enable developer mode in Odoo for additional debugging information and to access technical views.

## Development

### Prerequisites
- Odoo 18.0+
- Python 3.8+
- Modern web browser with JavaScript enabled

### File Structure
```
ubx_report_builder/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py
├── models/
│   ├── __init__.py
│   ├── ubx_report_builder.py
│   └── report_builder_field.py
├── views/
│   ├── report_builder_views.xml
│   ├── report_builder_field_views.xml
│   ├── report_builder_menus.xml
│   └── report_builder_templates.xml
├── static/src/
│   ├── css/
│   │   └── ubx_report_builder.css
│   ├── js/
│   │   ├── report_builder_widget.js
│   │   ├── field_selector.js
│   │   ├── drag_drop_builder.js
│   │   └── report_preview.js
│   └── xml/
│       └── report_builder_templates.xml
├── security/
│   ├── ir.model.access.csv
│   └── report_builder_security.xml
├── data/
│   └── report_builder_data.xml
└── demo/
    └── report_builder_demo.xml
```

## License

This module is licensed under LGPL-3. See LICENSE file for details.

## Support

For support and questions:
- Create an issue in the project repository
- Contact: support@inventionstech.com
- Documentation: [Module Documentation](https://docs.inventionstech.com/report-builder)

## Credits

Developed by **Inventions Technologies**
- Website: https://inventionstech.com
- Email: info@inventionstech.com

## Changelog

### Version 18.0.1.0.0
- Initial release
- Basic report building functionality
- Drag and drop interface
- Excel export
- OWL framework integration
- Security groups and access controls

---

**Happy Reporting! 📊**

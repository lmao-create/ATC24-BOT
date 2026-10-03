# Web Dashboard for Application Management

A modern, responsive web interface for managing Discord bot applications on localhost.

## Features

### 📊 Dashboard
- Real-time statistics and overview
- Total applications count
- Pending, approved, and rejected application counts
- Approval rate percentage
- Average review time in hours
- Recent applications overview

### 📝 Applications
- View all applications with filtering by status (pending, approved, rejected)
- Detailed application information display
- Review applications with a modal interface
- Add reviewer notes and decision
- Real-time status updates

### ⏰ Reminders
- View all pending applications
- See how long each application has been pending
- Schedule automatic reminders for pending reviews
- Configurable reminder intervals (hourly, daily, weekly, etc.)

### 📥 Export
- Export applications to CSV format
- Export applications to Excel format
- Includes all application data and review information
- Timestamped export files

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the web dashboard:
```bash
python web_dashboard.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Viewing Applications
1. Click on "Applications" in the sidebar
2. Filter by status using the dropdown menu
3. Click "View Details" or "Review" on any application card

### Reviewing Applications
1. Click "Review" on a pending application or go to Reminders and click "Review Now"
2. Select Approve or Reject
3. Add optional review notes
4. Enter your name as the reviewer
5. Click "Submit Review"

### Setting Up Reminders
1. Go to "Reminders" section
2. Set the desired check interval (in hours)
3. Click "Update Schedule"
4. The system will print reminders to console at specified intervals

### Exporting Data
1. Go to "Export" section
2. Click "Download CSV" or "Download Excel"
3. File will be downloaded with timestamp

## File Structure

```
web_dashboard/
├── web_dashboard.py       # Flask backend server
├── templates/
│   └── dashboard.html     # Main dashboard HTML
├── static/
│   ├── css/
│   │   └── style.css      # Dashboard styles
│   └── js/
│       └── script.js      # Dashboard functionality
└── README.md              # This file
```

## API Endpoints

### GET /api/applications
Get all applications with optional status filter
- Query: `status` (all, pending, approved, rejected)

### GET /api/applications/<app_id>
Get a specific application details

### POST /api/applications/<app_id>/review
Review and approve/reject an application
- Body: `{ decision, notes, reviewer }`

### GET /api/statistics
Get application statistics

### GET /api/reminders
Get pending applications for review

### POST /api/reminders/schedule
Schedule reminder checks
- Body: `{ hours }`

### GET /api/export/csv
Export applications as CSV

### GET /api/export/excel
Export applications as Excel

## Data Files

The dashboard reads from and writes to:
- `applications_data.json` - Application submissions
- `applications_config.json` - Configuration settings

## Requirements

- Python 3.8+
- Flask 3.0.0+
- pandas 2.0.0+
- openpyxl 3.1.0+
- schedule 1.2.0+

See `requirements.txt` for complete list.

## Configuration

The dashboard uses the same data files as the Discord bot cog:
- Reads/writes application data from `applications_data.json`
- Reads configuration from `applications_config.json`

## Troubleshooting

### Port 5000 already in use
Change the port in `web_dashboard.py`:
```python
app.run(debug=True, port=5001)  # Change 5000 to another port
```

### Template not found error
Ensure the `templates` folder exists and contains `dashboard.html`

### Static files not loading
Ensure the `static` folder structure exists:
- `static/css/style.css`
- `static/js/script.js`

### Applications not showing
1. Verify `applications_data.json` exists and has data
2. Check browser console for errors (F12)
3. Verify the bot has saved applications

## Performance Notes

- Dashboard auto-refreshes every 30 seconds
- Large datasets (100+ applications) may take a moment to load
- Export operations process all applications in memory

## Security Considerations

- Currently runs on localhost without authentication
- For production use, add:
  - Authentication/authorization
  - HTTPS/SSL
  - Rate limiting
  - CORS restrictions
  - Input validation

## Future Enhancements

- User authentication
- Application templates/categories
- Email notifications
- Advanced filtering and search
- Application history and audit logs
- Bulk operations (approve/reject multiple)
- Custom report generation

---

Made with ❤️ for Discord bot application management

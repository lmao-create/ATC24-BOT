# Discord Bot 🤖

A feature-rich Discord bot built with discord.py featuring music playback, moderation, economy, and more.

## Features

### 🎵 Music Player
- Play songs from YouTube by search 
- Queue management with skip, pause, resume
- Now-playing display in channel topic
- Support for yt-dlp for robust video downloading

### 🛡️ Moderation
- Ban, kick, mute, and unmute members
- Warning system with persistent storage
- Message purge with optional user filtering
- Admin-only warn clearing

### 💰 Economy
- Currency system for users
- Customizable economy commands

### 🎉 Fun & Entertainment
- Fun commands for community engagement

### 📊 Logging
- Guild activity logging and tracking

### 👋 Welcome System
- Customizable welcome messages
- Member join notifications

### 📝 Applications
- Modal-based application form (name, email, reason, experience)
- User submissions with automatic DM notifications
- Admin review and approval/rejection system
- Configurable results channel for posting decisions
- Application history and status tracking

### 🎫 Tickets
- Support ticket system with categories (general, bug, feature, support)
- User ticket creation and management
- Admin ticket assignment and status tracking
- Priority levels (low, medium, high, urgent)
- Comments and notes on tickets
- Ticket history and statistics

## Requirements

- Python 3.8+
- FFmpeg (for audio playback)
- Discord.py 2.3.2+
- yt-dlp for YouTube integration

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lmao-create/discord-bot.git
   cd discord-bot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # or
   source venv/bin/activate      # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Discord bot token
   ```

5. **Install FFmpeg** (required for music)
   - **Windows**: Download from https://ffmpeg.org/download.html or use `choco install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`

## Running the Bot

**Start the Discord Bot:**
```bash
python Bot.py
```

The bot will start and connect to Discord. All cogs will be loaded automatically from the `COGS` folder.

**Start the Web Dashboard (Optional):**
```bash
python web_dashboard.py
```

Access the dashboard at `http://localhost:5000` to manage applications through a web interface.

## Web Dashboard

The bot includes a modern web dashboard for managing applications on localhost. 

**Features:**
- 📊 Real-time statistics and analytics
- 📝 View and review all applications
- ⏰ Scheduled reminders for pending reviews
- 📥 Export to CSV or Excel
- 🎨 Modern, responsive interface
- 🎫 Ticket management and viewing

**Quick Start:**
```bash
python web_dashboard.py
```
Then visit `http://localhost:5000`

### Web Dashboard - Full Documentation

#### Features

##### 📊 Dashboard
- Real-time statistics and overview
- Total applications count
- Pending, approved, and rejected application counts
- Approval rate percentage
- Average review time in hours
- Recent applications overview

##### 📝 Applications
- View all applications with filtering by status (pending, approved, rejected)
- Detailed application information display
- Review applications with a modal interface
- Add reviewer notes and decision
- Real-time status updates

##### 🎫 Tickets
- View all support tickets with status filtering
- Ticket cards showing priority and metadata
- Update ticket status and priority
- Add comments to tickets
- View ticket statistics

##### ⏰ Reminders
- View all pending applications
- See how long each application has been pending
- Schedule automatic reminders for pending reviews
- Configurable reminder intervals (hourly, daily, weekly, etc.)

##### 📥 Export
- Export applications to CSV format
- Export applications to Excel format
- Includes all application data and review information
- Timestamped export files

#### Installation

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

#### Usage

##### Viewing Applications
1. Click on "Applications" in the sidebar
2. Filter by status using the dropdown menu
3. Click "View Details" or "Review" on any application card

##### Reviewing Applications
1. Click "Review" on a pending application or go to Reminders and click "Review Now"
2. Select Approve or Reject
3. Add optional review notes
4. Enter your name as the reviewer
5. Click "Submit Review"

##### Managing Tickets
1. Go to "Tickets" section
2. Filter by status (Open, In Progress, Closed)
3. Click "View & Edit" on any ticket
4. Update status/priority and add comments
5. Save changes

##### Setting Up Reminders
1. Go to "Reminders" section
2. Set the desired check interval (in hours)
3. Click "Update Schedule"
4. The system will print reminders to console at specified intervals

##### Exporting Data
1. Go to "Export" section
2. Click "Download CSV" or "Download Excel"
3. File will be downloaded with timestamp

#### API Endpoints

##### Applications
- `GET /api/applications` - Get all applications with optional status filter
  - Query: `status` (all, pending, approved, rejected)
- `GET /api/applications/<app_id>` - Get a specific application details
- `POST /api/applications/<app_id>/review` - Review and approve/reject
  - Body: `{ decision, notes, reviewer }`
- `GET /api/statistics` - Get application statistics
- `GET /api/export/csv` - Export applications as CSV
- `GET /api/export/excel` - Export applications as Excel

##### Tickets
- `GET /api/tickets` - Get all tickets with optional status filter
  - Query: `status` (all, open, in_progress, closed)
- `GET /api/tickets/<ticket_id>` - Get a specific ticket
- `POST /api/tickets/<ticket_id>/update` - Update ticket status/priority
  - Body: `{ status, priority, assigned_to }`
- `POST /api/tickets/<ticket_id>/comment` - Add comment to ticket
- `GET /api/tickets/statistics` - Get ticket statistics

##### Reminders
- `GET /api/reminders` - Get pending applications for review
- `POST /api/reminders/schedule` - Schedule reminder checks
  - Body: `{ hours }`

#### Configuration

The dashboard uses the same data files as the Discord bot:
- Reads/writes application data from `applications_data.json`
- Reads configuration from `applications_config.json`
- Reads/writes ticket data from `tickets_data.json`
- Reads configuration from `tickets_config.json`

#### Troubleshooting

##### Port 5000 already in use
Change the port in `web_dashboard.py`:
```python
app.run(debug=True, port=5001)  # Change 5000 to another port
```

##### Template not found error
Ensure the `templates` folder exists and contains `dashboard.html`

##### Static files not loading
Ensure the `static` folder structure exists:
- `static/css/style.css`
- `static/js/script.js`

##### Applications/Tickets not showing
1. Verify data JSON files exist and have data
2. Check browser console for errors (F12)
3. Verify the bot has saved data

#### Performance Notes

- Dashboard auto-refreshes every 30 seconds
- Large datasets (100+ items) may take a moment to load
- Export operations process all data in memory

#### Security Considerations

- Currently runs on localhost without authentication
- For production use, add:
  - Authentication/authorization
  - HTTPS/SSL
  - Rate limiting
  - CORS restrictions
  - Input validation

## Hosting Options

You can host this bot on various platforms:

### 1. **Local Machine**
- Simplest option for testing
- Requires your PC to stay on 24/7
- Works great for small communities
- No additional setup needed

### 2. **Heroku** (Free tier discontinued)
- ~~Previously free, now paid only~~
- Good for reliable uptime
- Easy deployment with git push

### 3. **Replit** (Recommended for beginners)
- Free tier available
- No credit card required
- Simple deployment
- Keep-alive options available
- Visit: https://replit.com

**Steps for Replit:**
1. Fork this repo to GitHub
2. Go to Replit.com and create new project
3. Import from GitHub
4. Add `.env` file with your TOKEN
5. Run `pip install -r requirements.txt`
6. Click Run to start the bot
7. Use UptimeRobot (free) to keep it alive

### 4. **PythonAnywhere**
- Free tier available
- Reliable hosting
- Good for 24/7 uptime
- Visit: https://www.pythonanywhere.com

**Steps for PythonAnywhere:**
1. Create account on PythonAnywhere
2. Upload bot files via web interface or git clone
3. Create a new web app (or console app)
4. Install requirements: `pip install -r requirements.txt`
5. Run in a bash console: `python Bot.py`
6. Use always-on feature for 24/7 uptime

### 5. **AWS, Google Cloud, Azure** (Paid)
- Professional hosting solutions
- Scalable and reliable
- More expensive but enterprise-grade
- Free tier available for new users

### 6. **VPS/Dedicated Server** (Paid)
- Full control over environment
- Better performance
- Providers: DigitalOcean, Linode, Vultr, etc.
- Typical cost: $5-20/month

**Steps for DigitalOcean Droplet:**
1. Create a droplet (Ubuntu 20.04+)
2. SSH into your server
3. Clone this repository
4. Install Python 3.8+: `sudo apt-get install python3 python3-pip`
5. Install FFmpeg: `sudo apt-get install ffmpeg`
6. Install requirements: `pip3 install -r requirements.txt`
7. Create `.env` file with your TOKEN
8. Run bot in background using `nohup` or `screen`

### 7. **Docker Container** (Advanced)
For containerized deployment on any platform.

**Create a `Dockerfile`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "Bot.py"]
```

**Build and run:**
```bash
docker build -t discord-bot .
docker run -d -e TOKEN=your_token discord-bot
```

### Recommendation
- **For testing**: Local machine or Replit
- **For small communities**: Replit or PythonAnywhere
- **For serious projects**: VPS (DigitalOcean) or Docker
- **For scaling**: AWS/Google Cloud/Azure

## Commands

### Music Commands
- `/play <song_name_or_url>` - Play a song from YouTube
- `/skip` - Skip to the next song
- `/stop` - Stop music and clear queue
- `/pause` - Pause the current song
- `/resume` - Resume paused song
- `/queue` - View the current music queue
- `/leave` - Disconnect from voice channel

### Moderation Commands
- `/ban <member> [reason]` - Ban a member
- `/kick <member> [reason]` - Kick a member
- `/mute <member> <duration>` - Mute a member (e.g., 1h, 30m)
- `/unmute <member> [reason]` - Unmute a member
- `/warn <member> [reason]` - Warn a member
- `/warns <member>` - View member's warnings
- `/clear_warns <member>` - Clear all warnings (admin only)
- `/unban <user> [reason]` - Unban a user
- `/purge <amount> [member]` - Delete messages

### Application Commands
**User Commands:**
- `/apply` - Submit an application via modal form
- `/myapplications` - View your submitted applications
- `/viewapplication <id>` - View details of a specific application
- `/deleteapplication <id>` - Delete one of your applications

**Admin Commands:**
- `/allapplications` - View all applications with summary and recent submissions
- `/reviewapplication <id> <decision>` - Approve or reject an application
- `/clearapplications` - Delete all applications (admin only)
- `/setresultschannel <channel>` - Configure where decisions are posted
- `/viewresultschannel` - View current results channel
- `/clearresultschannel` - Remove results channel configuration
- `/setapplicationpanel <channel>` - Create a persistent application panel in a channel
- `/viewapplicationpanel` - View current application panel settings

### Ticket Commands
**User Commands:**
- `/createticket <title> <description> [category]` - Create a support ticket
- `/mytickets` - View your submitted tickets
- `/viewticket <id>` - View ticket details
- `/closeticket <id>` - Close one of your tickets

**Admin Commands:**
- `/alltickets` - View all tickets with summary (admin only)
- `/setticketpanel <channel>` - Create a persistent ticket panel in a channel
- `/viewticketpanel` - View current ticket panel settings
- `/deleteticketpanel` - Remove the ticket panel (admin only)

## Project Structure

```
discord-bot/
├── Bot.py              # Main bot entry point
├── web_dashboard.py    # Flask web dashboard server
├── COGS/               # Bot command modules
│   ├── Music.py        # Music player commands
│   ├── Moderation.py   # Moderation commands
│   ├── ECO.py          # Economy commands
│   ├── Fun.py          # Fun commands
│   ├── Logs.py         # Logging commands
│   ├── Welcome.py      # Welcome system
│   ├── Applications.py # Application management system
│   ├── ApplicationsPanel.py # Application panel UI
│   ├── Tickets.py      # Support ticket system
│   └── TicketsPanel.py # Ticket panel UI
├── templates/          # Web dashboard templates
│   └── dashboard.html  # Main dashboard UI
├── static/             # Web dashboard static files
│   ├── css/
│   │   └── style.css   # Dashboard styling
│   └── js/
│       └── script.js   # Dashboard functionality
├── .env.example        # Example environment file
├── .gitignore          # Git ignore rules
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── WEB_DASHBOARD_README.md # Dashboard documentation
```

## Configuration

### Environment Variables
Create a `.env` file in the root directory:
```
TOKEN=your_discord_bot_token
```

Get your bot token from the [Discord Developer Portal](https://discord.com/developers/applications).

### Data Files
The bot stores data in JSON files:
- `warns_data.json` - Warning records
- `economy_data.json` - User currency/economy data
- `welcome_config.json` - Welcome system configuration
- `applications_data.json` - Submitted applications
- `applications_config.json` - Application system configuration (results channel)
- `applications_panel_config.json` - Application panel configuration (channel and message IDs)
- `tickets_data.json` - Support tickets
- `tickets_config.json` - Tickets system configuration
- `tickets_panel_config.json` - Ticket panel configuration (channel and message IDs)

## Troubleshooting

### "davey library needed" error
This means FFmpeg or audio libraries are missing. Install them:
```bash
pip install discord.py[voice]
```

### SSL Certificate errors on Windows
This is a known Windows issue. Try:
```bash
pip install certifi
python -m certifi
```

### Bot won't connect to Discord
- Verify your TOKEN in `.env` is correct
- Check that the bot has the necessary intents enabled in Developer Portal
- Ensure the bot has been invited to your server with appropriate permissions

## Permissions

For the bot to work properly, ensure it has these permissions:
- Send Messages
- Manage Messages (for purge)
- Manage Channels (for topic updates)
- Connect to Voice
- Speak in Voice Channels
- Use Application Commands

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for complete details.

## Support

For issues or questions, please open an issue on GitHub.

---

Made with ❤️ using discord.py

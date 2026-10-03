# ATC24 Discord Bot ✈️

A feature-rich **Discord bot built for ATC24 servers, virtual airlines, and aviation communities**. The bot provides flight-plan submissions, dispatcher review, pilot progression, moderation, economy, tickets, applications, logging, and other community-management features.

> **ATC24-focused:** The flight operations system is designed specifically around ATC24 flight proof and community operations.

## ✈️ ATC24 Flight Operations

### Flight Plan System
- `/flightplan` — Submit an ATC24 flight for dispatcher approval.
- Requires departure, arrival, flight number, aircraft, and a screenshot/proof attachment.
- Screenshot proof is stored with the submission.
- Optional notes can be included.
- Submissions are stored persistently with a unique Flight Plan ID.
- Duplicate/invalid submissions are protected against.
- Submissions are sent to the configured dispatcher review channel.
- Review buttons support **Approve**, **Reject**, and reviewed-submission cleanup.
- Rejections can include a reason.
- Approval records the dispatcher, timestamp, flight information, and proof URL.
- Approval/rejection state survives bot restarts.

### Dispatcher Review
Only members with the configured **Dispatcher** role can approve or reject flight plans.

Dispatchers can use:
- `/flightplan-view <id>` — Inspect a flight-plan submission.
- Review buttons — Approve or reject directly from the review message.

A pilot cannot approve their own submission.

### Pilot Rank Progression

Approved flights only count toward rank progression:

| Approved Flights | Rank | Additional Requirement |
|---:|---|---|
| 1+ | Junior F/O | None |
| 20+ | Senior F/O | None |
| 30+ | Junior Captain | None |
| 35+ | SFO | SFO written exam must be passed |

The SFO rank is **not** automatically awarded at 35 flights without the written exam.

### Pilot Profiles & Rank Management
- `/pilotprofile` — View an ATC24 pilot's approved-flight count, rank, and exam status.
- `/sync-ranks` — Recalculate configured pilot ranks.
- SFO written-exam staff functionality is included for updating exam status.

Rank role IDs are configured through environment variables rather than hardcoded into the bot.

## 🤖 General Bot Features

### 🎵 Music Player
- Play songs from YouTube by search
- Queue management with skip, pause, and resume
- Now-playing information
- yt-dlp integration

### 🛡️ Moderation
- Ban, kick, mute, and unmute members
- Warning system
- Message purge
- Administrative warning management

### 💰 Economy
- User currency system
- Customizable economy commands

### 🎉 Fun & Entertainment
- Community-focused fun commands

### 📊 Logging
- Guild activity logging and tracking

### 👋 Welcome System
- Customizable welcome messages
- Member join notifications

### 📝 Applications
- Modal-based applications
- Automatic DM notifications
- Admin review and approval/rejection
- Configurable results channel
- Application history and status tracking

### 🎫 Tickets
- Support tickets with categories
- User ticket creation and management
- Admin assignment
- Priority levels
- Ticket comments and notes
- Ticket history and statistics

---

## 📋 ATC24 Configuration

The flight-plan system uses environment variables for server-specific configuration.

```env
DISPATCHER_ROLE_ID=
FLIGHTPLAN_REVIEW_CHANNEL_ID=1555988863799795833
FLIGHTPLAN_LOG_CHANNEL_ID=

JUNIOR_FO_ROLE_ID=
SENIOR_FO_ROLE_ID=
JUNIOR_CAPTAIN_ROLE_ID=
SFO_ROLE_ID=

FLIGHTPLAN_DB_PATH=flightplans.db
```

The Discord bot token should also be stored in `.env` according to the main bot configuration.

**Never commit `.env` or your Discord bot token to GitHub.**

### Discord Permissions

The bot may require:

- View Channels
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Use Application Commands
- Manage Messages
- Manage Roles

For automatic pilot-rank roles, the bot's highest role must be above the configured pilot-rank roles in the Discord role hierarchy.

---

## 📦 Requirements

- Python 3.8+
- discord.py 2.3.2+
- FFmpeg for music functionality
- yt-dlp for YouTube integration
- SQLite for the ATC24 flight-plan database

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/lmao-create/discord-bot.git
cd discord-bot
```

### 2. Create a virtual environment

**Windows:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure `.env`

Create a `.env` file and add your bot token and ATC24 configuration.

Example:

```env
TOKEN=your_discord_bot_token

DISPATCHER_ROLE_ID=your_dispatcher_role_id
FLIGHTPLAN_REVIEW_CHANNEL_ID=1555988863799795833
FLIGHTPLAN_LOG_CHANNEL_ID=your_log_channel_id

JUNIOR_FO_ROLE_ID=your_junior_fo_role_id
SENIOR_FO_ROLE_ID=your_senior_fo_role_id
JUNIOR_CAPTAIN_ROLE_ID=your_junior_captain_role_id
SFO_ROLE_ID=your_sfo_role_id

FLIGHTPLAN_DB_PATH=flightplans.db
```

Do not publish your real token.

### 5. Start the bot

```bash
python Bot.py
```

Cogs are loaded automatically from the `COGS` directory.

---

## 💾 Database

The ATC24 flight-plan system uses SQLite for persistent flight records.

The database stores information such as:

- Pilot profiles
- Approved flight counts
- Written-exam status
- Flight-plan submissions
- Submission status
- Flight information
- Proof screenshot URL
- Dispatcher reviewer
- Approval/rejection timestamps
- Rejection reasons

The database file should be stored on persistent storage when deploying the bot to a hosting provider.

---

## 🌐 Hosting

The bot can run on:

- A local Windows/Linux machine
- Railway
- Render background workers
- A VPS
- Docker
- Other platforms that support persistent Python background processes

If using SQLite, make sure the host provides **persistent storage** so flight-plan records are not lost when the service restarts or redeploys.

---

## 📖 Commands

### ✈️ ATC24 Flight Operations

| Command | Description |
|---|---|
| `/flightplan` | Submit an ATC24 flight for dispatcher approval |
| `/pilotprofile` | View a pilot's ATC24 profile |
| `/flightplan-view <id>` | Inspect a flight-plan submission |
| `/sync-ranks` | Recalculate pilot rank roles |

### 🎵 Music

| Command | Description |
|---|---|
| `/play` | Play music |
| `/skip` | Skip the current song |
| `/stop` | Stop music and clear the queue |
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/queue` | View the queue |
| `/leave` | Leave the voice channel |

### 🛡️ Moderation

| Command | Description |
|---|---|
| `/ban` | Ban a member |
| `/kick` | Kick a member |
| `/mute` | Mute a member |
| `/unmute` | Unmute a member |
| `/warn` | Warn a member |
| `/warns` | View warnings |
| `/clear_warns` | Clear warnings |
| `/unban` | Unban a user |
| `/purge` | Delete messages |

> Additional commands may be available depending on the enabled cogs in the repository.

---

## 📁 Project Structure

```text
discord-bot/
├── Bot.py
├── COGS/
│   ├── FlightPlans.py
│   ├── Music.py
│   ├── Moderation.py
│   ├── ECO.py
│   ├── Fun.py
│   ├── Logs.py
│   ├── Welcome.py
│   ├── Applications.py
│   ├── ApplicationsPanel.py
│   ├── Tickets.py
│   └── TicketsPanel.py
├── flightplans.db
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── LICENSE
```

The exact files and cogs may vary between releases.

---

## 🔐 Security

- Keep your Discord bot token private.
- Never commit `.env` to GitHub.
- Use environment variables for secrets and server-specific IDs.
- Give the bot only the Discord permissions it requires.
- Ensure rank roles are correctly positioned beneath the bot's highest role.
- Back up the flight-plan database when using SQLite.

If a Discord token has ever been exposed publicly, revoke and regenerate it through the Discord Developer Portal.

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome.

When submitting changes:

1. Keep ATC24 functionality compatible with existing systems.
2. Do not expose tokens or other secrets.
3. Preserve the existing license.
4. Clearly describe significant changes in your pull request.

---

## 📄 License

This project is **not licensed under the MIT License**.

It is distributed under the **ATC24 Non-Commercial License**.

The software may be used, copied, modified, and distributed for personal, educational, or non-commercial ATC24 community purposes.

**Commercial use is prohibited without prior written permission from the copyright holder.**

See [`LICENSE`](LICENSE) for the complete license terms.

---

## ❤️ Credits

Built with:

- [discord.py](https://discordpy.readthedocs.io/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)

Designed for **ATC24 servers, virtual airlines, and aviation communities**.

---

Made with ❤️ for the ATC24 community.

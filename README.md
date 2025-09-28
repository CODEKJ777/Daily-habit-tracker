# 🤖 AI-Powered Habit & Task Tracker

A modern, AI-enhanced habit and task tracking application with both CLI and web interfaces. Built with Python, Flask, and TailwindCSS.

## ✨ Features

### Core MVP (CLI)
- ✅ Add and track daily habits
- ✅ Mark habits as complete with streak tracking
- ✅ Add and manage daily tasks
- ✅ Mark tasks as complete
- ✅ View today's progress summary
- ✅ Beautiful terminal interface with emojis

### AI Assistant Layer
- 🤖 AI-powered greetings and motivation
- 🧠 Personalized habit insights and analysis
- 📋 Smart task prioritization
- 💡 Suggested new habits based on your patterns
- 🎯 Streak analysis and encouragement

### Web MVP (Flask + TailwindCSS)
- 🌐 Modern, responsive web dashboard served by Flask
- 📱 Mobile-friendly design
- 🎨 Beautiful UI with TailwindCSS
- ⚡ Real-time updates for habits, tasks, and AI insights
- 🔄 Interactive habit and task management
- 📊 Visual progress tracking and streak displays

## 🚀 Quick Start

### Option 1: CLI Version (Recommended for Quick Use)

```bash
# Run the CLI application
python main.py
```

**Features:**
- Interactive menu system
- AI-powered insights
- Streak tracking
- Beautiful terminal interface

### Option 2: Web Version (Modern Dashboard)

```bash
# Start the Flask backend
python backend/app.py
```

Then open: **http://localhost:5000**

**Features:**
- Modern web dashboard
- Real-time AI insights
- Responsive design
- Interactive habit/task management

## 📁 Project Structure

```
Daily Habit & Task Tracker/
├── main.py                 # CLI entry point (if still used)
├── data.json               # Data storage (Legacy CLI version for migration)
├── requirements.txt        # Python dependencies
│
└── backend/                # Flask web backend
    ├── app.py              # Flask application
    ├── database.py         # SQLite database setup and connection
    ├── models.py           # Data models (Habit, Task, Completion)
    ├── ai_service.py       # AI integration service
    ├── services.py         # Business logic and database interactions (HabitService, TaskService, StatsService)
    ├── config.py           # Backend configuration
    ├── static/             # Static files (CSS, JS)
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       ├── ai.js
    │       └── app.js
    └── templates/          # Flask templates
        └── index.html      # Main web dashboard
```

## 🎨 Modern Dashboard Features

### Design Highlights
- **Minimal & Clean**: Notion/Trello-like design
- **Responsive**: Works on mobile and desktop
- **Interactive**: Hover effects and smooth animations
- **Modern Icons**: Lucide icons throughout
- **Beautiful Gradients**: Eye-catching color schemes

### Key Sections
1. **Header**: AI greeting banner with motivational message
2. **Sidebar**: Navigation and quick stats
3. **Habits Section**: Interactive habit cards with streak tracking
4. **Tasks Section**: Task management with priority tags
5. **AI Assistant**: Insights, prioritization, and suggestions

### Interactive Elements
- ✅ Click habits to mark as complete
- ➕ Add new habits and tasks
- 🔄 Refresh AI insights
- 📊 Real-time progress updates
- 🔔 Toast notifications

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd "Daily Habit & Task Tracker – Phase 1 Mvp"
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up AI (Optional)**
Create a `.env` file in the root directory:
```env
OPENROUTER_API_KEY=your_api_key_here
# or
ANTHROPIC_API_KEY=your_api_key_here
```

## 📱 Usage Examples

### CLI Version
```bash
# Run the CLI application
python main.py
```
**Note:** The CLI version is primarily for initial setup or migration. The main functionality is now focused on the Web Version.

### Web Version
1. Start the backend: `python backend/app.py`
2. Open browser: `http://localhost:5000`
3. Use the modern dashboard interface

## 🎯 Current Status

Your application is **fully functional** with:

- ✅ **4/6 habits completed today** (as shown in demo)
- ✅ **AI Assistant working** (HabBot providing insights)
- ✅ **Streak tracking** (3-day streak for water intake)
- ✅ **Task management** (4 tasks for today)
- ✅ **Web interface ready** (Flask backend)

## 🔧 Customization

### Adding New Features
- **New Habits/Tasks**: Modify `backend/services.py` for logic and `backend/models.py` for data structure.
- **AI Prompts**: Update `backend/ai_service.py` for different AI responses.
- **UI Changes**: Modify `backend/templates/index.html` and `backend/static/js/app.js` for web interface.
- **Styling**: Update TailwindCSS classes in `backend/templates/index.html` or `backend/static/css/style.css`.

### Configuration
- **AI Settings**: Edit `backend/config.py` or `.env` for AI behavior.
- **Database**: Modify `backend/database.py` for data setup and connection.
- **API Endpoints**: Add new routes in `backend/app.py`.

## 🚀 Deployment

### Local Development
```bash
# CLI version
python main.py

# Web version
python backend/app.py
```

### Production Deployment
1. Set up a production server
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Run with a production WSGI server like Gunicorn

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built with ❤️ and AI
- Icons by [Lucide](https://lucide.dev/)
- Styling with [TailwindCSS](https://tailwindcss.com/)
- AI powered by OpenRouter/Claude

---

**Ready to build better habits? Start with the CLI version for quick use, or launch the web dashboard for a modern experience! 🚀**


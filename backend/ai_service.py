# AI integration (adapted from CLI)
#!/usr/bin/env python3
"""
AI Service for Web Version of Habit Tracker
Adapted from CLI version for Flask backend integration
"""

import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from database import get_db_connection
from services import HabitService, TaskService, StatsService

# Load environment variables
load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# Prefer env override; fall back to a cheaper, widely accessible model
DEFAULT_AI_MODEL = os.getenv("DEFAULT_AI_MODEL", "anthropic/claude-3-haiku")
AI_ASSISTANT_NAME = "HabBot"
AI_PERSONALITY = "encouraging, motivational, and insightful"

# Use shared DB connection from backend.database to avoid duplicate DB paths


def _friendly_error(status_code: int) -> str:
    if status_code == 401:
        return "❌ AI is disabled: invalid or missing API key. Add your key in .env and restart."
    if status_code == 402:
        return "💳 AI unavailable: payment required or no credits for this model. Add credits or switch to a cheaper model."
    if status_code == 429:
        return "⏳ AI rate limit reached. Please try again in a moment."
    if status_code == 503:
        return "🚧 AI service temporarily unavailable. Please try again later."
    return "❌ AI service error. We'll show a helpful fallback for now."


def call_ai_api(prompt: str, system_prompt: str = None) -> str:
    """Call AI API (OpenRouter or direct Anthropic)"""
    try:
        if OPENROUTER_API_KEY:
            return call_openrouter(prompt, system_prompt)
        elif ANTHROPIC_API_KEY:
            return call_anthropic(prompt, system_prompt)
        else:
            return "❌ No AI API key configured. Please set up your API key in .env"
    except Exception as e:
        return f"❌ AI service unavailable: {str(e)}"


def call_openrouter(prompt: str, system_prompt: str = None) -> str:
    """Call OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/habit-tracker-web",
        "X-Title": "Habit & Task Tracker Web AI",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": DEFAULT_AI_MODEL,
        "messages": messages,
        "max_tokens": 300,
        "temperature": 0.7,
    }

    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers=headers,
        json=data,
        timeout=30,
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    # Graceful mapping for common issues
    friendly = _friendly_error(response.status_code)
    return friendly


def call_anthropic(prompt: str, system_prompt: str = None) -> str:
    """Call direct Anthropic API"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }

    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }

    if system_prompt:
        data["system"] = system_prompt

    response = requests.post(
        "https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=30
    )

    if response.status_code == 200:
        return response.json()["content"][0]["text"]
    # Graceful mapping for common issues
    friendly = _friendly_error(response.status_code)
    return friendly


def get_daily_greeting() -> str:
    """Generate personalized daily greeting for web dashboard"""
    try:
        stats = StatsService.get_daily_stats_for_ai()

        system_prompt = f"""You are {AI_ASSISTANT_NAME}, a {AI_PERSONALITY} AI assistant for habit tracking. 
        Keep responses warm, concise (2-3 sentences), and motivational. Perfect for web dashboard greeting."""

        user_prompt = f"""Create a personalized greeting for the user's dashboard.
        
        Current status:
        - Habits completed today: {stats['habits_done_today']}/{stats['total_habits']}
        - Tasks completed today: {stats['tasks_done_today']}/{stats['total_tasks_today']}
        - Best current streak: {stats['best_streak']} days
        - Active habit streaks: {stats['active_streaks']}
        - Day: {datetime.now().strftime('%A')}
        
        Make it encouraging and specific to their progress. Keep it under 40 words for web display."""

        return call_ai_api(user_prompt, system_prompt)

    except Exception as e:
        # Fallback greeting if AI fails
        return f"Good {get_time_of_day()}! Ready to build some amazing habits today? 🌟"


def get_time_of_day() -> str:
    """Get appropriate time greeting"""
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    else:
        return "evening"


def get_habit_insights() -> str:
    """Analyze habits and provide insights for web dashboard"""
    try:
        habits = StatsService.get_all_habits_for_insights()

        if not habits:
            return "💡 Ready to start your habit journey? Add your first habit to begin building an amazing routine!"

        # Analyze patterns
        streak_analysis = []
        for habit in habits:
            name = habit["name"]
            streak = habit["streak"]

            if streak >= 7:
                streak_analysis.append(f"🔥 {name}: {streak}-day streak (excellent!)")
            elif streak >= 3:
                streak_analysis.append(
                    f"💪 {name}: {streak}-day streak (building momentum)"
                )
            elif streak == 0:
                streak_analysis.append(f"⭕ {name}: needs attention")
            else:
                streak_analysis.append(f"🌱 {name}: {streak}-day streak (good start)")

        system_prompt = f"""You are {AI_ASSISTANT_NAME}, providing habit insights for a web dashboard.
        Be encouraging but honest. Give 1-2 specific, actionable suggestions. Keep under 60 words."""

        user_prompt = f"""Analyze these habit patterns and provide brief insights:
        
        {chr(10).join(streak_analysis)}
        
        Provide encouraging analysis and 1 specific suggestion for improvement."""

        return call_ai_api(user_prompt, system_prompt)

    except Exception as e:
        return (
            "📊 Great habits take time to build. Focus on consistency over perfection!"
        )


def get_task_prioritization() -> str:
    """Analyze tasks and suggest priorities for web dashboard"""
    try:
        pending_tasks = StatsService.get_pending_tasks()

        if not pending_tasks:
            return "🎉 No pending tasks for today! Perfect time to work on your habits or plan ahead."

        system_prompt = f"""You are {AI_ASSISTANT_NAME}, helping with task prioritization for a web app.
        Suggest which tasks to tackle first. Be concise and practical. Keep under 50 words."""

        task_list = "\n".join([f"- {task['name']}" for task in pending_tasks])

        user_prompt = f"""Help prioritize these pending tasks:
        
        {task_list}
        
        Suggest which 1-2 tasks to focus on first and briefly why."""

        return call_ai_api(user_prompt, system_prompt)

    except Exception as e:
        return "📋 Tackle your most important task first - you've got this!"


def suggest_new_habit() -> str:
    """Suggest a new habit based on existing ones for web interface"""
    try:
        existing_habit_names = StatsService.get_existing_habit_names()

        system_prompt = f"""You are {AI_ASSISTANT_NAME}, suggesting complementary habits for a web app.
        Suggest ONE specific, small habit. Keep under 50 words and be actionable."""

        if existing_habit_names:
            habits_list = ", ".join(existing_habit_names)
            user_prompt = f"""Based on these existing habits: {habits_list}
            
            Suggest ONE new small habit that would complement these well. Keep it simple and achievable."""
        else:
            user_prompt = "Suggest ONE simple, beginner-friendly habit for someone just starting their habit-building journey."

        return call_ai_api(user_prompt, system_prompt)

    except Exception as e:
        return "💡 Try starting with 'Drink a glass of water when you wake up' - simple and effective!"


def get_motivational_message(context: str = "general") -> str:
    """Get contextual motivational message for web interface"""
    system_prompt = f"""You are {AI_ASSISTANT_NAME}, providing motivation for a web app.
    Keep it under 30 words, uplifting, and specific to the context."""

    if context == "new_habit":
        user_prompt = "The user just added a new habit. Provide encouraging words for starting strong."
    elif context == "habit_completed":
        user_prompt = (
            "The user just completed a habit. Celebrate and encourage consistency."
        )
    elif context == "task_completed":
        user_prompt = "The user completed a task. Celebrate their productivity."
    elif context == "streak_broken":
        user_prompt = "A habit streak was broken. Provide encouraging words about getting back on track."
    else:
        user_prompt = (
            "Provide a general motivational message about building good habits."
        )

    try:
        return call_ai_api(user_prompt, system_prompt)
    except:
        # Fallback messages
        fallback_messages = {
            "new_habit": "Great choice! Start small and stay consistent - you've got this! 🌟",
            "habit_completed": "Awesome work! Every day you stick to your habits, you're becoming stronger! 💪",
            "task_completed": "Task completed! You're making great progress today! ✨",
            "streak_broken": "No worries! Every expert was once a beginner. Tomorrow is a fresh start! 🌅",
            "general": "Small consistent actions lead to remarkable results. Keep going! 🚀",
        }
        return fallback_messages.get(context, fallback_messages["general"])


def get_weekly_summary() -> str:
    """Generate weekly progress summary for web dashboard"""
    try:
        stats = StatsService.get_weekly_summary_stats()

        system_prompt = f"""You are {AI_ASSISTANT_NAME}, providing a weekly summary for a web dashboard.
        Be celebratory and encouraging. Keep under 60 words."""

        user_prompt = f"""Create a brief weekly summary:
        
        - Habit completions this week: {stats['weekly_completions']}
        - Tasks completed this week: {stats['weekly_tasks']}
        - Currently active streaks: {stats['active_streaks']}
        
        Celebrate progress and encourage continued effort."""

        return call_ai_api(user_prompt, system_prompt)

    except Exception as e:
        return "📊 This week you've made progress on your journey. Every step counts - keep it up! 🌟"


def get_smart_notification(notification_type: str = "daily") -> str:
    """Generate smart notifications for web app"""
    try:
        if notification_type == "daily":
            return get_daily_greeting()
        elif notification_type == "evening":
            # Evening reflection
            system_prompt = f"""You are {AI_ASSISTANT_NAME}, providing an evening reflection message.
            Be reflective and prepare them for tomorrow. Keep under 40 words."""

            user_prompt = "Create an encouraging evening message that reflects on today and motivates for tomorrow."
            return call_ai_api(user_prompt, system_prompt)
        else:
            return get_motivational_message("general")

    except Exception as e:
        return "🌙 Take a moment to appreciate what you accomplished today. Tomorrow brings new opportunities!"


# Health check function
def check_ai_service() -> dict:
    """Check AI service status"""
    has_api_key = bool(OPENROUTER_API_KEY or ANTHROPIC_API_KEY)

    if not has_api_key:
        return {
            "status": "disabled",
            "message": "No API key configured",
            "features_available": False,
        }

    try:
        # Test with a simple prompt
        test_response = call_ai_api("Say 'AI service is working'")
        if "working" in test_response.lower():
            return {
                "status": "online",
                "message": "AI service is ready",
                "features_available": True,
                "model": DEFAULT_AI_MODEL,
            }
        else:
            return {
                "status": "error",
                "message": "Unexpected AI response",
                "features_available": False,
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"AI service error: {str(e)}",
            "features_available": False,
        }

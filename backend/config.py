# Configuration management
#!/usr/bin/env python3
"""
Configuration management for AI-Powered Habit Tracker
Handles environment variables, API settings, and app configuration
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class"""

    # Flask Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Database Configuration
    DATABASE_FILE = os.getenv("DATABASE_FILE", "habit_tracker.db")
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")

    # AI Service Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    DEFAULT_AI_MODEL = os.getenv("DEFAULT_AI_MODEL", "anthropic/claude-3.5-sonnet")
    AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "30"))
    AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "300"))
    AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))

    # AI Assistant Settings
    AI_ASSISTANT_NAME = os.getenv("AI_ASSISTANT_NAME", "HabBot")
    AI_PERSONALITY = os.getenv(
        "AI_PERSONALITY", "encouraging, motivational, and insightful"
    )

    # Application Settings
    APP_NAME = os.getenv("APP_NAME", "AI Habit Tracker")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

    # CORS Settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # Notification Settings
    NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "True").lower() == "true"

    # Rate Limiting (for future implementation)
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "False").lower() == "true"
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100 per hour")

    # Timezone Settings
    TIMEZONE = os.getenv("TIMEZONE", "UTC")

    # Backup Settings
    AUTO_BACKUP = os.getenv("AUTO_BACKUP", "False").lower() == "true"
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "habit_tracker.log")

    @property
    def ai_enabled(self):
        """Check if AI features are available"""
        return bool(self.OPENROUTER_API_KEY or self.ANTHROPIC_API_KEY)

    @property
    def database_path(self):
        """Get absolute database path"""
        return os.path.abspath(self.DATABASE_FILE)

    def validate_config(self):
        """Validate critical configuration settings"""
        issues = []

        # Check AI configuration
        if not self.ai_enabled:
            issues.append("⚠️  No AI API key configured - AI features will be disabled")

        # Check secret key in production
        if (
            self.FLASK_ENV == "production"
            and self.SECRET_KEY == "dev-secret-key-change-in-production"
        ):
            issues.append("🚨 SECRET_KEY must be changed in production!")

        # Check database path
        db_dir = os.path.dirname(self.database_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception as e:
                issues.append(f"❌ Cannot create database directory: {e}")

        return issues


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    FLASK_ENV = "production"

    # Stricter security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Enable auto-backup in production
    AUTO_BACKUP = True


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    DATABASE_FILE = ":memory:"  # Use in-memory database for tests
    SECRET_KEY = "test-secret-key"
    AI_ENABLED = False  # Disable AI during tests


# Configuration mapping
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    return config_map.get(config_name, config_map["default"])


def print_config_status():
    """Print configuration status for debugging"""
    config = get_config()

    print(f"\n🔧 Configuration Status:")
    print(f"   Environment: {config.FLASK_ENV}")
    print(f"   Debug Mode: {config.DEBUG}")
    print(f"   AI Enabled: {config().ai_enabled}")
    print(f"   Database: {config.DATABASE_FILE}")
    print(f"   AI Model: {config.DEFAULT_AI_MODEL}")
    print(f"   Assistant: {config.AI_ASSISTANT_NAME}")

    # Check for issues
    issues = config().validate_config()
    if issues:
        print(f"\n⚠️  Configuration Issues:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print(f"\n✅ Configuration looks good!")


# Environment variable defaults for .env file generation
ENV_TEMPLATE = """# AI-Powered Habit Tracker Configuration
# Copy this to .env and configure your settings

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
DEBUG=True

# Notifications
NOTIFICATIONS_ENABLED=True

# Database
DATABASE_FILE=habit_tracker.db

# AI Services (Choose one)
# Option 1: OpenRouter (supports multiple AI models)
OPENROUTER_API_KEY=your-openrouter-key-here

# Option 2: Direct Anthropic API
# ANTHROPIC_API_KEY=your-anthropic-key-here

# AI Configuration
DEFAULT_AI_MODEL=anthropic/claude-3.5-sonnet
AI_ASSISTANT_NAME=HabBot
AI_PERSONALITY=encouraging, motivational, and insightful
AI_REQUEST_TIMEOUT=30
AI_MAX_TOKENS=300
AI_TEMPERATURE=0.7

# Application Settings
APP_NAME=AI Habit Tracker
APP_VERSION=1.0.0

# Security & CORS
CORS_ORIGINS=*

# Features
AUTO_BACKUP=False
BACKUP_RETENTION_DAYS=30
TIMEZONE=UTC

# Logging
LOG_LEVEL=INFO
LOG_FILE=habit_tracker.log
"""


def create_env_template():
    """Create .env template file if it doesn't exist"""
    env_file = ".env.example"

    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write(ENV_TEMPLATE)
        print(f"✅ Created {env_file} - copy to .env and configure your settings")

    # Also check if .env exists
    if not os.path.exists(".env"):
        print(
            f"⚠️  No .env file found. Copy {env_file} to .env and configure your API keys"
        )


if __name__ == "__main__":
    # When run directly, show config status and create template
    create_env_template()
    print_config_status()

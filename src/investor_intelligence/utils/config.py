"""Configuration management for Investor Intelligence Agent."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AppConfig(BaseModel):
    name: str = "Investor Intelligence Agent"
    version: str = "1.0.0"
    debug: bool = False


class MCPConfig(BaseModel):
    host: str = "localhost"
    port: int = 8000
    name: str = "investor-intelligence"


class GoogleConfig(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8080/callback"
    sheets_scopes: list = ["https://www.googleapis.com/auth/spreadsheets"]
    gmail_scopes: list = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]


class DatabaseConfig(BaseModel):
    url: str = "sqlite:///investor_intelligence.db"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/investor_intelligence.log"


class Config:
    """Main configuration class."""

    def __init__(self, config_file: str = "config/config.yaml"):
        self.config_file = Path(config_file)
        self._config_data = self._load_config()

        # Initialize configuration sections
        self.app = AppConfig(**self._config_data.get("app", {}))
        self.mcp = MCPConfig(**self._config_data.get("mcp", {}).get("server", {}))
        self.google = GoogleConfig(
            client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            **self._config_data.get("google", {}),
        )
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///investor_intelligence.db")
        )
        self.logging = LoggingConfig(**self._config_data.get("logging", {}))

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            print(f"Config file {self.config_file} not found. Using defaults.")
            return {}

        try:
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading config file: {e}")
            return {}


# Global configuration instance
config = Config()

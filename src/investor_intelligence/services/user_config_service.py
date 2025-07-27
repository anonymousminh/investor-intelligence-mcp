import sqlite3
import json
import os
from typing import Dict, Any


class UserConfigService:
    """Service for managing user-specific configurations and preferences."""

    DB_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "data",
        "user_configs.db",
    )

    def __init__(self):
        self._create_table()

    def _create_table(self):
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_configs (
                user_id TEXT NOT NULL,
                portfolio_id TEXT,
                config_json TEXT NOT NULL,
                PRIMARY KEY (user_id, portfolio_id)
            )
        """
        )
        conn.commit()
        conn.close()

    def save_user_config(
        self, user_id: str, config: Dict[str, Any], portfolio_id: str = None
    ):
        """Saves or updates the configuration for a given user and optional portfolio.

        Args:
            user_id (str): The ID of the user.
            config (Dict[str, Any]): A dictionary containing the user's configuration. If 'risk_profile' is not present, it will be set to 'moderate' by default.
            portfolio_id (str, optional): The ID of the portfolio. If None, saves as a global user config.
        """
        # Ensure risk_profile is present
        if "risk_profile" not in config:
            config["risk_profile"] = "moderate"
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()
        config_json = json.dumps(config)
        cursor.execute(
            "INSERT OR REPLACE INTO user_configs (user_id, portfolio_id, config_json) VALUES (?, ?, ?)",
            (user_id, portfolio_id, config_json),
        )
        conn.commit()
        conn.close()

    def get_user_config(self, user_id: str, portfolio_id: str = None) -> Dict[str, Any]:
        """Retrieves the configuration for a given user and optional portfolio.

        Args:
            user_id (str): The ID of the user.
            portfolio_id (str, optional): The ID of the portfolio. If None, retrieves global user config.

        Returns:
            Dict[str, Any]: A dictionary containing the user's configuration, or an empty dict if not found.
        """
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT config_json FROM user_configs WHERE user_id = ? AND portfolio_id IS ?",
            (user_id, portfolio_id),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return {}


if __name__ == "__main__":
    config_service = UserConfigService()
    test_user_id = "user_config_test_123"

    # Test saving configuration
    initial_config = {
        "alert_frequency": "daily",
        "email_notifications": True,
        "min_price_change_alert": 1.5,
        "preferred_news_sources": ["Reuters", "Bloomberg"],
    }
    config_service.save_user_config(test_user_id, initial_config)
    print(f"Saved config for {test_user_id}: {initial_config}")

    # Test retrieving configuration
    retrieved_config = config_service.get_user_config(test_user_id)
    print(f"Retrieved config for {test_user_id}: {retrieved_config}")

    # Test updating configuration
    updated_config = retrieved_config
    updated_config["alert_frequency"] = "weekly"
    updated_config["preferred_news_sources"].append("Wall Street Journal")
    config_service.save_user_config(test_user_id, updated_config)
    print(f"Updated config for {test_user_id}: {updated_config}")

    # Verify update
    verified_config = config_service.get_user_config(test_user_id)
    print(f"Verified updated config for {test_user_id}: {verified_config}")

    # Test non-existent user
    non_existent_config = config_service.get_user_config("non_existent_user")
    print(f"Config for non-existent user: {non_existent_config}")

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import time
import atexit

from investor_intelligence.services.summary_service import SummaryService
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.services.monitoring_service import MonitoringService
from investor_intelligence.services.portfolio_service import PortfolioService
from investor_intelligence.services.nlp_service import NLPService
from investor_intelligence.services.query_processor_service import QueryProcessorService
from investor_intelligence.tools.gmail_tool import (
    send_message,
    get_gmail_service,
    create_message,
)
from investor_intelligence.models.portfolio import Portfolio, StockHolding
from investor_intelligence.ml.relevance_model import RelevanceModel
from datetime import date, datetime
import shutil
from investor_intelligence.utils.logging import logger
import os

# Initialize services (ensure portfolio_service is configured with your Google Sheet ID)
alert_service = AlertService()
relevance_model = RelevanceModel()
monitoring_service = MonitoringService(alert_service, relevance_model)
summary_service = SummaryService(alert_service, monitoring_service)
nlp_service = NLPService()

# Placeholder for user data (in a real app, this would come from a user management system)
USERS_TO_MONITOR = [
    {
        "user_id": "user_abc",
        "email": "anhminh7802@gmail.com",
        "portfolio_name": "My Main Portfolio",
    },
    # Add more users as needed
]

# IMPORTANT: Replace with your actual Google Sheet ID and range for each user's portfolio
# This is a simplified example. In a real application, portfolio mapping would be more robust.
PORTFOLIO_MAPPING = {
    "user_abc": {
        "spreadsheet_id": "16Bi8WR-mn5ggPZsGmu3Yr3XAg_S7LaZqDhdy2D6x35Q",
        "range_name": "Sheet1!A1:D",
    },
}


def get_user_email_by_id(user_id: str) -> str:
    for user_data in USERS_TO_MONITOR:
        if user_data["user_id"] == user_id:
            return user_data["email"]
    return None


def get_user_id_by_email(email: str) -> str:
    for user_data in USERS_TO_MONITOR:
        if user_data["email"] == email:
            return user_data["user_id"]
    return None


def send_daily_intelligence_summary():
    logger.info(f"--- Running daily intelligence summary job at {datetime.now()} ---")
    for user_data in USERS_TO_MONITOR:
        user_id = user_data["user_id"]
        user_email = user_data["email"]
        portfolio_name = user_data["portfolio_name"]

        portfolio_config = PORTFOLIO_MAPPING.get(user_id)
        if not portfolio_config:
            logger.warning(
                f"No portfolio configuration found for user {user_id}. Skipping."
            )
            continue

        portfolio_service = PortfolioService(
            portfolio_config["spreadsheet_id"], portfolio_config["range_name"]
        )
        portfolio = portfolio_service.load_portfolio_from_sheets(
            user_id, portfolio_name
        )

        if portfolio:
            logger.info(f"Generating summary for {user_id} - {portfolio.name}...")
            daily_summary = summary_service.generate_daily_summary(user_id, portfolio)
            gmail_service = get_gmail_service()
            sender_email = "me"  # 'me' refers to the authenticated user
            message = create_message(
                sender_email,
                user_email,
                f"Daily Investor Intelligence Summary - {datetime.now().strftime('%Y-%m-%d')}",
                daily_summary,
            )
            send_message(gmail_service, sender_email, message)
        else:
            logger.warning(
                f"Could not load portfolio for user {user_id}. Skipping summary generation."
            )


def send_weekly_intelligence_summary():
    logger.info(f"--- Running weekly intelligence summary job at {datetime.now()} ---")
    for user_data in USERS_TO_MONITOR:
        user_id = user_data["user_id"]
        user_email = user_data["email"]
        portfolio_name = user_data["portfolio_name"]

        portfolio_config = PORTFOLIO_MAPPING.get(user_id)
        if not portfolio_config:
            logger.warning(
                f"No portfolio configuration found for user {user_id}. Skipping weekly summary."
            )
            continue

        portfolio_service = PortfolioService(
            portfolio_config["spreadsheet_id"], portfolio_config["range_name"]
        )
        portfolio = portfolio_service.load_portfolio_from_sheets(
            user_id, portfolio_name
        )

        if portfolio:
            logger.info(
                f"Generating weekly summary for {user_id} - {portfolio.name}..."
            )
            weekly_summary = summary_service.generate_weekly_summary(user_id, portfolio)
            send_email(
                user_email,
                f"Weekly Investor Intelligence Summary - {datetime.now().strftime('%Y-%m-%d')}",
                weekly_summary,
            )
        else:
            logger.warning(
                f"Could not load portfolio for user {user_id}. Skipping weekly summary generation."
            )


def process_incoming_email_queries():
    logger.info(f"--- Processing incoming email queries at {datetime.now()} ---")
    # Fetch unread emails that might be queries
    # You might want to filter by sender or subject more strictly in a real app
    unread_emails = get_unread_emails(
        query="is:unread subject:(stock OR query OR portfolio OR price OR earnings OR news)"
    )

    if unread_emails:
        query_processor = QueryProcessorService(
            nlp_service, PortfolioService("", ""), monitoring_service
        )  # Initialize with dummy portfolio service for now
        for email in unread_emails:
            sender_email = email["sender"]
            # Attempt to map sender email to a user_id
            user_id = get_user_id_by_email(sender_email)
            if user_id:
                logger.info(
                    f"Processing query from {sender_email} (User ID: {user_id})..."
                )
                response_body = query_processor.process_email_query(
                    user_id, sender_email, email["body"]
                )
                send_email(sender_email, f"Re: {email['subject']}", response_body)
            else:
                logger.warning(f"Unknown sender: {sender_email}. Skipping query.")
    else:
        logger.info("No new email queries to process.")


def run_monitoring_jobs():
    logger.info(f"--- Running daily monitoring jobs at {datetime.now()} ---")
    for user_data in USERS_TO_MONITOR:
        user_id = user_data["user_id"]
        portfolio_name = user_data["portfolio_name"]
        portfolio_config = PORTFOLIO_MAPPING.get(user_id)
        if not portfolio_config:
            logger.warning(
                f"No portfolio configuration found for user {user_id}. Skipping monitoring."
            )
            continue
        portfolio_service = PortfolioService(
            portfolio_config["spreadsheet_id"], portfolio_config["range_name"]
        )
        portfolio = portfolio_service.load_portfolio_from_sheets(
            user_id, portfolio_name
        )
        if portfolio:
            logger.info(f"Monitoring for {user_id} - {portfolio.name}...")
            monitoring_service.monitor_earnings_reports(user_id, portfolio)
            monitoring_service.monitor_news_sentiment(user_id, portfolio)
            monitoring_service.monitor_price_changes(user_id, portfolio)
        else:
            logger.warning(
                f"Could not load portfolio for user {user_id}. Skipping monitoring."
            )

    def backup_database(db_path: str, backup_dir: str = "./backups"):
        """Creates a timestamped backup of a SQLite database file."""
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = os.path.basename(db_path)
        backup_path = os.path.join(backup_dir, f"{db_name}.{timestamp}.bak")
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Successfully backed up {db_name} to {backup_path}")
        except Exception as e:
            logger.error(f"Error backing up {db_name}: {e}")


if __name__ == "__main__":
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        lambda: backup_database(AlertService.DB_FILE), CronTrigger(hour=3, minute=0)
    )  # Daily backup at 3 AM
    scheduler.add_job(
        lambda: backup_database(UserConfigService.DB_FILE),
        CronTrigger(hour=3, minute=0),
    )  # Daily backup at 3 AM

    # Schedule daily monitoring (e.g., every day at 7:00 AM)
    scheduler.add_job(
        run_monitoring_jobs, CronTrigger(hour=7, minute=0, day_of_week="*")
    )

    # Schedule daily summary (e.g., every day at 8:00 AM)
    scheduler.add_job(
        send_daily_intelligence_summary, CronTrigger(hour=8, minute=0, day_of_week="*")
    )

    # Schedule weekly summary (e.g., every Monday at 9:00 AM)
    scheduler.add_job(
        send_weekly_intelligence_summary,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
    )

    # Schedule email query processing (e.g., every 5 minutes)
    scheduler.add_job(process_incoming_email_queries, CronTrigger(minute="*/5"))

    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to exit.")

    # Shut down the scheduler when the app exits
    atexit.register(lambda: scheduler.shutdown())

    while True:
        time.sleep(1)  # Keep the main thread alive

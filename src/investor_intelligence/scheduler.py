from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import time
import atexit

from investor_intelligence.services.summary_service import SummaryService
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.services.monitoring_service import MonitoringService
from investor_intelligence.services.portfolio_service import PortfolioService
from investor_intelligence.tools.gmail_tool import (
    send_message,
    get_gmail_service,
    create_message,
)
from investor_intelligence.models.portfolio import Portfolio, StockHolding
from datetime import date, datetime

# Initialize services (ensure portfolio_service is configured with your Google Sheet ID)
alert_service = AlertService()
monitoring_service = MonitoringService(alert_service)
summary_service = SummaryService(alert_service, monitoring_service)

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


def send_daily_intelligence_summary():
    print(f"\n--- Running daily intelligence summary job at {datetime.now()} ---")
    for user_data in USERS_TO_MONITOR:
        user_id = user_data["user_id"]
        user_email = user_data["email"]
        portfolio_name = user_data["portfolio_name"]

        portfolio_config = PORTFOLIO_MAPPING.get(user_id)
        if not portfolio_config:
            print(f"No portfolio configuration found for user {user_id}. Skipping.")
            continue

        portfolio_service = PortfolioService(
            portfolio_config["spreadsheet_id"], portfolio_config["range_name"]
        )
        portfolio = portfolio_service.load_portfolio_from_sheets(
            user_id, portfolio_name
        )

        if portfolio:
            print(f"Generating summary for {user_id} - {portfolio.name}...")
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
            print(
                f"Could not load portfolio for user {user_id}. Skipping summary generation."
            )


# Schedule the job to run every Monday at 9:00 AM
scheduler.add_job(send_weekly_intelligence_summary, CronTrigger(day_of_week=\'mon\', hour=9, minute=0))

def send_weekly_intelligence_summary():
    print(f"\n--- Running weekly intelligence summary job at {datetime.now()} ---")
    for user_data in USERS_TO_MONITOR:
        user_id = user_data["user_id"]
        user_email = user_data["email"]
        portfolio_name = user_data["portfolio_name"]

        portfolio_config = PORTFOLIO_MAPPING.get(user_id)
        if not portfolio_config:
            print(f"No portfolio configuration found for user {user_id}. Skipping weekly summary.")
            continue

        portfolio_service = PortfolioService(portfolio_config["spreadsheet_id"], portfolio_config["range_name"])
        portfolio = portfolio_service.load_portfolio_from_sheets(user_id, portfolio_name)

        if portfolio:
            print(f"Generating weekly summary for {user_id} - {portfolio.name}...")
            weekly_summary = summary_service.generate_weekly_summary(user_id, portfolio)
            send_email(user_email, f"Weekly Investor Intelligence Summary - {datetime.now().strftime("%Y-%m-%d")}", weekly_summary)
        else:
            print(f"Could not load portfolio for user {user_id}. Skipping weekly summary generation.")


# if __name__ == "__main__":
#     scheduler = BackgroundScheduler()

#     # Schedule the job to run every day at a specific time (e.g., 8:00 AM)
#     # Adjust the cron expression as needed (e.g., for weekly summaries)
#     scheduler.add_job(
#         send_daily_intelligence_summary, CronTrigger(hour=8, minute=0, day_of_week="*")
#     )

#     # Start the scheduler
#     scheduler.start()
#     print("Scheduler started. Press Ctrl+C to exit.")

#     # Shut down the scheduler when the app exits
#     atexit.register(lambda: scheduler.shutdown())

#     while True:
#         time.sleep(1)  # Keep the main thread alive

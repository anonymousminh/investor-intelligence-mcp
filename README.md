# Investor Intelligence Agent MCP Server

A Model Context Protocol (MCP) server for intelligent stock portfolio monitoring, analysis, and alerting. Integrates Google Sheets, Alpha Vantage, and Gmail to provide real-time insights, automated summaries, and actionable alerts for investors.

---

## Features

- **Stock Monitoring**: Track real-time and historical stock prices.
- **Portfolio Management**: Sync and analyze portfolios from Google Sheets.
- **Email Alerts**: Automated email notifications for portfolio events and summaries.
- **Market Analysis**: Trend analysis and portfolio optimization tools.
- **Scheduler**: Automated periodic tasks (e.g., weekly summaries).

---

## Tech Stack

- **Python 3.11**
- **MCP Framework** (custom, see `src/investor_intelligence/mcp.py`)
- **Google Sheets API**
- **Alpha Vantage API**
- **Gmail API**
- **SQLite** (for local data persistence, if used)
- **APScheduler** (for scheduled jobs)
- **OAuth 2.0** (for Google/Gmail authentication)
- **pytest** (for testing)
- **Docker** (optional, for containerization)

---

## Project Structure

```
investor-intelligence-mcp/
├── config/                # API credentials and config files
├── docs/                  # Documentation
├── src/
│   └── investor_intelligence/
│       ├── models/        # Data models (portfolio, alert, etc.)
│       ├── services/      # Business logic (portfolio, email, alert)
│       ├── tools/         # API integrations (sheets, alpha vantage, gmail)
│       ├── utils/         # Utility functions (auth, config, logging)
│       └── server.py      # MCP server entry point
├── tests/                 # Unit and integration tests
├── requirements.txt       # Python dependencies
├── environment.yml        # Conda environment (optional)
├── README.md
└── setup.py
```

---

## Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/investor-intelligence-mcp.git
   cd investor-intelligence-mcp
   ```

2. **Set up Python virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   Or use conda:

   ```bash
   conda env create -f environment.yml
   conda activate investor-intelligence
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   # Or, if using setup.py
   pip install -e .
   ```

4. **Configure API Keys and Credentials**
   - Place your Google Sheets and Gmail API credentials in `config/credentials.json`.
   - Get a free Alpha Vantage API key and set it as an environment variable:
     ```bash
     export ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
     ```
   - (Optional) Set Google Sheets ID and range as environment variables:
     ```bash
     export GOOGLE_SHEET_ID=your_sheet_id
     export GOOGLE_SHEET_RANGE="Sheet1!A1:D"
     ```

---

## How to Run

1. **Start the MCP Server**

   ```bash
   python -m src.investor_intelligence.server
   ```

   The server will initialize and register its tools.

2. **Interact with the Server**
   - You can call the server's tools programmatically (see `src/investor_intelligence/server.py` for examples):
   ```python
   from src.investor_intelligence.server import InvestorIntelligenceServer
   server = InvestorIntelligenceServer()
   price = server.get_stock_price("AAPL")
   print(price)
   ```
   - If you expose endpoints (e.g., via FastAPI or Flask), you can interact using HTTP requests (not included by default).

---

## Testing

Run all tests with:

```bash
pytest
```

- Tests are located in the `tests/` directory and cover services, tools, and server endpoints.
- Mocks are used for external APIs and authentication.

---

## Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements, bug fixes, or new features.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

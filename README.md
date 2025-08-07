# Investor Intelligence Agent MCP Server

A comprehensive Model Context Protocol (MCP) server for intelligent stock portfolio monitoring, analysis, and alerting. This system integrates Google Sheets, Alpha Vantage, Yahoo Finance, and Gmail to provide real-time insights, automated summaries, machine learning-powered relevance scoring, and actionable alerts for investors.

---

## ✨ Key Features

### 📊 **Portfolio Management**

- **Google Sheets Integration**: Sync and manage portfolios directly from Google Sheets
- **Real-time Portfolio Analytics**: Calculate performance metrics, gains/losses, and portfolio value
- **Multi-Portfolio Support**: Handle multiple portfolios per user with customizable configurations

### 🚨 **Intelligent Alerting System**

- **Smart Price Monitoring**: Track significant price movements with customizable thresholds
- **Earnings Calendar Alerts**: Automated notifications for upcoming earnings reports
- **News Sentiment Analysis**: Monitor news sentiment and generate relevant alerts
- **ML-Powered Relevance Scoring**: Machine learning model that learns from user feedback to improve alert relevance

### 🤖 **Machine Learning & Analytics**

- **Relevance Model**: Advanced ML model that predicts alert relevance based on user preferences and portfolio context
- **Feedback Learning**: Continuous improvement through user feedback integration
- **Performance Metrics**: Track model accuracy, precision, recall, and F1 scores

### 📧 **Communication & Reporting**

- **Automated Email Alerts**: Gmail integration for sending portfolio summaries and alerts
- **Weekly/Daily Summaries**: Scheduled portfolio performance reports
- **Customizable Notifications**: User-configurable alert preferences and thresholds

### 🌐 **Web Dashboard**

- **Flask-based Web Interface**: Interactive dashboard for portfolio visualization
- **Real-time Metrics**: Live portfolio performance and alert monitoring
- **User-friendly UI**: Modern interface for managing portfolios and viewing analytics

### 🔄 **Automation & Scheduling**

- **Background Monitoring**: Continuous portfolio and market monitoring
- **Scheduled Tasks**: Automated periodic summaries and alerts
- **Event-driven Architecture**: Responsive system that reacts to market changes

---

## 🛠 Tech Stack

### **Core Framework**

- **Python 3.11+**
- **MCP (Model Context Protocol)** - Custom implementation for tool orchestration
- **Flask** - Web application framework for dashboard
- **APScheduler** - Background task scheduling

### **APIs & Integrations**

- **Google Sheets API** - Portfolio data synchronization
- **Gmail API** - Email notifications and alerts
- **Alpha Vantage API** - Stock market data and earnings calendar
- **Yahoo Finance (yfinance)** - Additional market data and historical prices

### **Data & ML**

- **Peewee ORM** - Lightweight database management
- **Pydantic** - Data validation and serialization
- **Custom ML Pipeline** - Relevance scoring and feedback learning
- **Matplotlib** - Data visualization and charting

### **Development & Deployment**

- **pytest** - Comprehensive testing framework
- **Docker** - Containerization support
- **OAuth 2.0** - Secure Google API authentication
- **Gunicorn** - Production WSGI server

---

## 📁 Project Structure

```
investor-intelligence-mcp/
├── 📁 config/                    # API credentials and configuration files
├── 📁 data/                      # Data storage and cache
├── 📁 docs/                      # Documentation and architecture guides
│   └── architecture.md           # System architecture overview
├── 📁 examples/                  # Demo scripts and usage examples
│   ├── feedback_demo.py          # ML feedback system demonstration
│   ├── metrics_demo.py           # Portfolio metrics demonstration
│   └── 📁 data/                  # Sample data files
├── 📁 src/investor_intelligence/
│   ├── 📁 models/                # Data models and schemas
│   │   ├── portfolio.py          # Portfolio and stock holding models
│   │   ├── alert.py              # Alert and notification models
│   │   └── alert_feedback.py     # User feedback models
│   ├── 📁 services/              # Business logic and core services
│   │   ├── portfolio_service.py  # Portfolio management and analytics
│   │   ├── alert_service.py      # Alert generation and management
│   │   ├── monitoring_service.py # Market monitoring and price tracking
│   │   ├── analytics_service.py  # Performance analytics and calculations
│   │   ├── metrics_service.py    # System metrics and monitoring
│   │   ├── email_service.py      # Gmail integration and notifications
│   │   ├── nlp_service.py        # Natural language processing
│   │   └── user_config_service.py # User preferences and configurations
│   ├── 📁 tools/                 # External API integrations
│   │   ├── alpha_vantage_tool.py # Alpha Vantage API wrapper
│   │   ├── gmail_tool.py         # Gmail API integration
│   │   ├── news_tool.py          # News and sentiment analysis
│   │   └── sheets_tool.py        # Google Sheets API wrapper
│   ├── 📁 ml/                    # Machine learning components
│   │   └── relevance_model.py    # ML model for alert relevance scoring
│   ├── 📁 utils/                 # Utility functions and helpers
│   │   ├── auth.py               # Authentication and OAuth handlers
│   │   ├── config.py             # Configuration management
│   │   ├── db.py                 # Database utilities and connections
│   │   ├── logging.py            # Logging configuration
│   │   └── metrics.py            # Performance metrics utilities
│   ├── 📁 web_app/               # Flask web dashboard
│   │   ├── app.py                # Flask application entry point
│   │   ├── 📁 static/            # CSS, JS, and static assets
│   │   └── 📁 templates/         # HTML templates
│   ├── mcp.py                    # MCP server implementation
│   ├── server.py                 # Main server entry point
│   └── scheduler.py              # Background task scheduler
├── 📁 tests/                     # Comprehensive test suite
│   ├── 📁 unit/                  # Unit tests
│   ├── 📁 integration/           # Integration tests
│   ├── 📁 services/              # Service-level tests
│   ├── 📁 tools/                 # API integration tests
│   └── 📁 e2e/                   # End-to-end tests
├── requirements.txt              # Python dependencies
├── environment.yml               # Conda environment specification
├── setup.py                     # Package installation script
├── Dockerfile                   # Docker container configuration
└── README.md                    # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Google Cloud Project with APIs enabled (Sheets, Gmail)
- Alpha Vantage API key (free tier available)

### 1. **Clone and Setup Environment**

```bash
# Clone the repository
git clone https://github.com/yourusername/investor-intelligence-mcp.git
cd investor-intelligence-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Alternative: Using Conda**

```bash
conda env create -f environment.yml
conda activate investor-intelligence
```

### 2. **API Configuration**

#### **Google APIs Setup**

1. Create a Google Cloud Project
2. Enable Google Sheets API and Gmail API
3. Create OAuth 2.0 credentials
4. Download credentials and save as `config/credentials.json`

#### **Alpha Vantage Setup**

1. Get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Set environment variable:

```bash
export ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

#### **Portfolio Configuration**

Set up your Google Sheet with portfolio data:

```bash
export GOOGLE_SHEET_ID=your_sheet_id
export GOOGLE_SHEET_RANGE="Sheet1!A1:D"
```

**Expected Sheet Format:**
| Symbol | Quantity | Purchase Price | Purchase Date |
|--------|----------|----------------|---------------|
| AAPL | 100 | 150.00 | 2024-01-15 |
| GOOGL | 50 | 2800.00 | 2024-01-20 |

### 3. **Environment Variables**

Create a `.env` file in the project root:

```bash
# API Keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Google Sheets Configuration
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_SHEET_RANGE=your_sheet_range

# Email Configuration (optional)
SENDER_EMAIL=your_email@gmail.com
RECIPIENT_EMAIL=alerts@yourdomain.com

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
```

---

## 🏃 How to Run

### **Option 1: MCP Server (Recommended)**

Start the MCP server for tool integration:

```bash
# Navigate to the project directory
cd investor-intelligence-mcp

# Activate your virtual environment
source venv/bin/activate

# Start the MCP server
python -m src.investor_intelligence.server
```

The server will initialize and register all tools for portfolio monitoring, alerts, and analytics.

### **Option 2: Web Dashboard**

Launch the interactive web interface:

```bash
# Start the Flask web application
cd src/investor_intelligence/web_app
python app.py
```

Visit `http://localhost:5000` to access the dashboard featuring:

- 📊 Real-time portfolio performance
- 🚨 Active alerts and notifications
- 📈 Analytics and metrics visualization
- ⚙️ User configuration options

### **Option 3: Background Monitoring**

Run continuous portfolio monitoring:

```bash
# Start the scheduler for automated monitoring
python -m src.investor_intelligence.scheduler
```

This will:

- Monitor stock prices every 15 minutes
- Check for earnings announcements
- Generate and send email alerts
- Update portfolio analytics

### **Option 4: Docker Deployment**

Deploy using Docker for production:

```bash
# Build the Docker image
docker build -t investor-intelligence .

# Run the container
docker run -d \
  -p 5000:5000 \
  -e ALPHA_VANTAGE_API_KEY=your_key \
  -e GOOGLE_SHEET_ID=your_sheet_id \
  -v $(pwd)/config:/app/config \
  investor-intelligence
```

### **Programmatic Usage**

You can also use the system programmatically:

```python
from src.investor_intelligence.services.portfolio_service import PortfolioService
from src.investor_intelligence.services.monitoring_service import MonitoringService
from src.investor_intelligence.services.alert_service import AlertService

# Initialize services
portfolio_service = PortfolioService("your_sheet_id", "Sheet1!A1:D")
alert_service = AlertService()
monitoring_service = MonitoringService(alert_service, None)

# Load and analyze portfolio
portfolio = portfolio_service.load_portfolio_from_sheets("user_123", "My Portfolio")
monitoring_service.monitor_price_changes("user_123", portfolio)

# Get current stock price
from src.investor_intelligence.tools.alpha_vantage_tool import get_current_price
price = get_current_price("AAPL")
print(f"AAPL current price: ${price}")
```

---

## 🧪 Testing

### **Run All Tests**

```bash
# Run the complete test suite
pytest

# Run with coverage report
pytest --cov=src/investor_intelligence --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/e2e/          # End-to-end tests only
```

### **Test Structure**

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test service interactions and API integrations
- **End-to-End Tests**: Test complete workflows from portfolio loading to alert generation
- **Service Tests**: Test business logic and data processing
- **Tool Tests**: Test external API integrations with mocks

### **Test Coverage**

The test suite covers:

- ✅ Portfolio loading and analytics
- ✅ Alert generation and relevance scoring
- ✅ Email service integration
- ✅ Stock price monitoring
- ✅ ML model training and prediction
- ✅ Web dashboard functionality

---

## 📚 Examples & Demos

The `examples/` directory contains demonstration scripts:

### **Portfolio Metrics Demo**

```bash
python examples/metrics_demo.py
```

Demonstrates:

- Portfolio performance calculation
- Risk metrics and analytics
- Visualization of portfolio data

### **ML Feedback Demo**

```bash
python examples/feedback_demo.py
```

Demonstrates:

- ML relevance model training
- User feedback integration
- Model performance evaluation

### **Custom Integration Example**

```python
# examples/custom_integration.py
from src.investor_intelligence.services.portfolio_service import PortfolioService
from src.investor_intelligence.tools.alpha_vantage_tool import get_current_price

# Create custom monitoring workflow
def custom_portfolio_monitor():
    portfolio_service = PortfolioService("your_sheet_id", "Sheet1!A1:D")
    portfolio = portfolio_service.load_portfolio_from_sheets("user", "portfolio")

    for holding in portfolio.holdings:
        current_price = get_current_price(holding.symbol)
        gain_loss = (current_price - holding.purchase_price) * holding.quantity
        print(f"{holding.symbol}: ${gain_loss:.2f} gain/loss")

if __name__ == "__main__":
    custom_portfolio_monitor()
```

---

## 🔧 Configuration

### **User Preferences**

Configure alert thresholds and preferences:

```python
from src.investor_intelligence.services.user_config_service import UserConfigService

config_service = UserConfigService()
config_service.set_user_preference("user_123", {
    "min_price_change_alert": 2.0,  # Alert on 2%+ price changes
    "risk_profile": "moderate",      # Risk tolerance level
    "email_notifications": True,     # Enable email alerts
    "monitoring_frequency": "15min"  # Check every 15 minutes
})
```

### **System Configuration**

Customize system behavior in `src/investor_intelligence/utils/config.py`:

```python
# Alert thresholds
DEFAULT_PRICE_CHANGE_THRESHOLD = 5.0  # 5% price change
DEFAULT_VOLUME_THRESHOLD = 1.5         # 1.5x average volume

# Monitoring intervals
PRICE_CHECK_INTERVAL = 15 * 60         # 15 minutes
EARNINGS_CHECK_INTERVAL = 24 * 60 * 60 # 24 hours

# Email settings
MAX_DAILY_ALERTS = 10                  # Limit alerts per day
EMAIL_BATCH_SIZE = 5                   # Group alerts in batches
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help improve the Investor Intelligence Agent:

### **Getting Started**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### **Development Guidelines**

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Write unit tests for new features
- Update documentation as needed
- Use type hints where applicable

### **Areas for Contribution**

- 🧠 **Machine Learning**: Improve relevance scoring algorithms
- 📊 **Analytics**: Add new portfolio metrics and visualizations
- 🔧 **Integrations**: Add support for new brokers or data sources
- 🎨 **UI/UX**: Enhance the web dashboard design
- 📱 **Mobile**: Create mobile app integration
- 🔒 **Security**: Implement additional security measures
- 📈 **Performance**: Optimize data processing and API calls

### **Reporting Issues**

When reporting bugs, please include:

- Python version and OS
- Error messages and stack traces
- Steps to reproduce the issue
- Expected vs actual behavior

---

## 📖 API Reference

### **Core Services**

#### Portfolio Service

```python
from src.investor_intelligence.services.portfolio_service import PortfolioService

service = PortfolioService(sheet_id, range_name)
portfolio = service.load_portfolio_from_sheets(user_id, portfolio_name)
performance = service.calculate_performance(portfolio)
```

#### Alert Service

```python
from src.investor_intelligence.services.alert_service import AlertService

service = AlertService()
alerts = service.get_alerts_for_user(user_id, active_only=True)
service.create_alert(user_id, alert_type, message, metadata)
```

#### Monitoring Service

```python
from src.investor_intelligence.services.monitoring_service import MonitoringService

service = MonitoringService(alert_service, relevance_model)
service.monitor_price_changes(user_id, portfolio)
service.monitor_earnings_reports(user_id, portfolio)
```

### **Available Tools**

- `alpha_vantage_tool`: Stock prices, earnings calendar, market data
- `gmail_tool`: Send emails, manage notifications
- `sheets_tool`: Read/write Google Sheets data
- `news_tool`: Fetch news and sentiment analysis

---

## 🔍 Troubleshooting

### **Common Issues**

#### **Authentication Errors**

```bash
# Error: credentials.json not found
# Solution: Ensure Google API credentials are in config/credentials.json

# Error: OAuth2 flow failed
# Solution: Check that APIs are enabled in Google Cloud Console
```

#### **API Rate Limits**

```bash
# Error: Alpha Vantage API limit exceeded
# Solution: Implement caching or upgrade to premium plan

# Error: Google Sheets API quota exceeded
# Solution: Implement exponential backoff and request batching
```

#### **Missing Dependencies**

```bash
# Error: ModuleNotFoundError
# Solution: Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### **Debug Mode**

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🎯 Roadmap

### **Upcoming Features**

- [ ] **Mobile App**: React Native mobile application
- [ ] **Real-time Streaming**: WebSocket-based real-time price updates
- [ ] **Advanced ML**: Deep learning models for market prediction
- [ ] **Social Trading**: Share and follow other investors' strategies
- [ ] **Options Tracking**: Support for options and derivatives
- [ ] **Tax Optimization**: Automated tax-loss harvesting suggestions
- [ ] **News Integration**: Enhanced news sentiment analysis
- [ ] **Backtesting**: Historical portfolio performance simulation

### **Performance Improvements**

- [ ] **Caching Layer**: Redis integration for faster data access
- [ ] **Database Migration**: Move from SQLite to PostgreSQL
- [ ] **Microservices**: Split monolith into microservices architecture
- [ ] **CI/CD Pipeline**: Automated testing and deployment

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Alpha Vantage](https://www.alphavantage.co/) for providing stock market data
- [Google APIs](https://developers.google.com/) for Sheets and Gmail integration
- [Yahoo Finance](https://finance.yahoo.com/) for additional market data
- [Model Context Protocol](https://github.com/anthropics/mcp) for the MCP framework

---

## 📞 Support

- **Documentation**: Check the `docs/` directory for detailed guides
- **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/investor-intelligence-mcp/issues)
- **Discussions**: Join conversations on [GitHub Discussions](https://github.com/yourusername/investor-intelligence-mcp/discussions)
- **Email**: Contact the maintainers at support@yourdomain.com

---

_Built with ❤️ for the investment community_

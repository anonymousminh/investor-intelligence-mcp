# Architecture Overview

## System Architecture

The Investor Intelligence Agent follows a modular architecture with clear separation of concerns:

┌─────────────────┐
│ MCP Server │
├─────────────────┤
│ Tools │
├─────────────────┤
│ Services │
├─────────────────┤
│ Models │
├─────────────────┤
│ Utilities │
└─────────────────┘

## Components

### MCP Server Layer

- Handles client connections
- Manages tool registration and calls
- Provides async request/response handling

### Tools Layer

- Google Sheets integration
- Yahoo Finance API wrapper
- Gmail API integration

### Services Layer

- Portfolio management logic
- Alert generation and processing
- Email service coordination

### Models Layer

- Data structures for portfolio, alerts, and configurations
- Pydantic models for validation

### Utilities Layer

- Configuration management
- Authentication handling
- Logging setup

## Data Flow

1. Client connects to MCP server
2. Server calls appropriate tools based on requests
3. Tools use services to process business logic
4. Services interact with external APIs
5. Results are returned through the MCP protocol

## Future Enhancements

- Database layer for persistence
- Machine learning models for predictions
- WebSocket support for real-time updates
- Multi-user support with authentication

"""Test MCP server functionality."""

import pytest
from unittest.mock import AsyncMock, patch
from src.investor_intelligence.server import InvestorIntelligenceServer


@pytest.fixture
def server():
    """Create a test server instance."""
    return InvestorIntelligenceServer()


def test_server_initialization(server):
    """Test that server initializes correctly."""
    assert server.server.name == "investor-intelligence"


@pytest.mark.asyncio
async def test_get_portfolio_status(server):
    """Test portfolio status tool."""
    result = await server._get_portfolio_status({})

    assert result.content[0].text.startswith("Portfolio status:")
    assert not result.isError


@pytest.mark.asyncio
async def test_check_alerts(server):
    """Test alert checking tool."""
    result = await server._check_alerts({})

    assert "No alerts" in result.content[0].text
    assert not result.isError


@pytest.mark.asyncio
async def test_send_summary(server):
    """Test summary sending tool."""
    result = await server._send_summary(
        {"email": "test@example.com", "period": "weekly"}
    )

    assert "test@example.com" in result.content[0].text
    assert not result.isError

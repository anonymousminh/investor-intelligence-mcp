"""Main MCP server for Investor Intelligence Agent."""

import asyncio
import logging
from typing import Any, Sequence
from mcp import Server, ServerRequestContext
from mcp.types import TextContent, Tool, CallToolResult
from pydantic import BaseModel, Field

from .utils.config import config
from .utils.logging import logger


class InvestorIntelligenceServer:
    """Main MCP server class for Investor Intelligence Agent."""

    def __init__(self):
        self.server = Server("investor-intelligence")
        self._setup_tools()
        self._setup_handlers()

    def _setup_tools(self):
        """Register MCP tools."""

        # Portfolio monitoring tool
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="get_portfolio_status",
                    description="Get current portfolio status and holdings",
                    inputSchema={"type": "object", "properties": {}, "required": []},
                ),
                Tool(
                    name="check_alerts",
                    description="Check for new alerts and notifications",
                    inputSchema={"type": "object", "properties": {}, "required": []},
                ),
                Tool(
                    name="send_summary",
                    description="Send portfolio summary via email",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Email address to send summary to",
                            },
                            "period": {
                                "type": "string",
                                "description": "Time period for summary (daily, weekly, monthly)",
                                "enum": ["daily", "weekly", "monthly"],
                            },
                        },
                        "required": ["email"],
                    },
                ),
            ]

    def _setup_handlers(self):
        """Set up tool call handlers."""

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: dict[str, Any], context: ServerRequestContext
        ) -> CallToolResult:
            """Handle tool calls."""

            logger.info(f"Tool called: {name} with arguments: {arguments}")

            try:
                if name == "get_portfolio_status":
                    return await self._get_portfolio_status(arguments)
                elif name == "check_alerts":
                    return await self._check_alerts(arguments)
                elif name == "send_summary":
                    return await self._send_summary(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True,
                )

    async def _get_portfolio_status(self, arguments: dict) -> CallToolResult:
        """Get portfolio status (placeholder implementation)."""
        # TODO: Implement actual portfolio status checking
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="Portfolio status: Server initialized successfully! Integration with Google Sheets, Yahoo Finance, and Gmail will be implemented in the next phases.",
                )
            ]
        )

    async def _check_alerts(self, arguments: dict) -> CallToolResult:
        """Check for alerts (placeholder implementation)."""
        # TODO: Implement actual alert checking
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="No alerts at this time. Alert system will be implemented in Phase 2.",
                )
            ]
        )

    async def _send_summary(self, arguments: dict) -> CallToolResult:
        """Send portfolio summary (placeholder implementation)."""
        email = arguments.get("email")
        period = arguments.get("period", "weekly")

        # TODO: Implement actual email sending
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Summary for {period} period would be sent to {email}. Email integration will be implemented in Phase 2.",
                )
            ]
        )


def main():
    """Main function to start the MCP server."""
    logger.info("Starting Investor Intelligence MCP Server...")
    logger.info(f"Configuration: {config.app.name} v{config.app.version}")

    # Create server instance
    server_instance = InvestorIntelligenceServer()

    logger.info(f"Server initialized on {config.mcp.host}:{config.mcp.port}")
    logger.info("Server ready to accept connections")

    # Run the server
    asyncio.run(server_instance.server.run())


if __name__ == "__main__":
    main()

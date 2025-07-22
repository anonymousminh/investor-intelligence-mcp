import re


class NLPService:
    """Service for processing natural language queries related to stocks and portfolios."""

    def extract_stock_symbols(self, text: str) -> list:
        """Extracts potential stock symbols from a given text.

        Args:
            text (str): The input text.

        Returns:
            list: A list of extracted stock symbols (e.g., ["AAPL", "MSFT"]).
        """
        # Simple regex to find uppercase words that might be stock symbols
        # This can be improved with a dictionary of known symbols or more complex NLP
        symbols = re.findall(r"\b[A-Z]{2,5}\b", text.upper())
        # Expanded list of common English words and phrases to filter out
        common_words = {
            "AND",
            "THE",
            "FOR",
            "BUY",
            "SELL",
            "WHAT",
            "HOW",
            "IS",
            "ARE",
            "MY",
            "YOUR",
            "PRICE",
            "OF",
            "TELL",
            "ME",
            "ABOUT",
            "NEWS",
            "SHOW",
            "CURRENT",
            "LATEST",
            "REPORT",
            "WHEN",
            "NEXT",
            "QUOTE",
            "VALUE",
            "ARTICLE",
            "HEADLINE",
            "HOLDINGS",
            "INVESTMENTS",
            "PORTFOLIO",
        }
        # For even better accuracy, consider using a set of valid stock symbols from an exchange
        return [s for s in symbols if s not in common_words]

    def identify_query_type(self, text: str) -> str:
        """Identifies the type of query based on keywords.

        Args:
            text (str): The input text.

        Returns:
            str: "price_query", "earnings_query", "news_query", "portfolio_query", or "unknown".
        """
        text_lower = text.lower()
        if "price" in text_lower or "quote" in text_lower or "value" in text_lower:
            return "price_query"
        elif (
            "earnings" in text_lower
            or "report" in text_lower
            or "calendar" in text_lower
        ):
            return "earnings_query"
        elif (
            "news" in text_lower or "article" in text_lower or "headline" in text_lower
        ):
            return "news_query"
        elif (
            "portfolio" in text_lower
            or "holdings" in text_lower
            or "my investments" in text_lower
        ):
            return "portfolio_query"
        else:
            return "unknown"


if __name__ == "__main__":
    nlp_service = NLPService()

    # Test stock symbol extraction
    print("\n--- Testing stock symbol extraction ---")
    text1 = "What is the current price of AAPL and MSFT?"
    print(f'Text: "{text1}" -> Symbols: {nlp_service.extract_stock_symbols(text1)}')

    text2 = "Tell me about the latest news for GOOG and TSLA."
    print(f'Text: "{text2}" -> Symbols: {nlp_service.extract_stock_symbols(text2)}')

    text3 = "What is the latest news and history price of NVDA?"
    print(f'Text: "{text3}" -> Symbols: {nlp_service.extract_stock_symbols(text3)}')

    # Test query type identification
    print("\n--- Testing query type identification ---")
    query1 = "What is the current price of IBM?"
    print(f'Query: "{query1}" -> Type: {nlp_service.identify_query_type(query1)}')

    query2 = "When is the next earnings report for NVDA?"
    print(f'Query: "{query2}" -> Type: {nlp_service.identify_query_type(query2)}')

    query3 = "Show me the latest news about Amazon."
    print(f'Query: "{query3}" -> Type: {nlp_service.identify_query_type(query3)}')

    query4 = "What are my current portfolio holdings?"
    print(f'Query: "{query4}" -> Type: {nlp_service.identify_query_type(query4)}')

    query5 = "Hello, how are you?"
    print(f'Query: "{query5}" -> Type: {nlp_service.identify_query_type(query5)}')

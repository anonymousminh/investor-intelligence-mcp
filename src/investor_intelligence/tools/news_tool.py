import os
import requests
from datetime import datetime, timedelta

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_BASE_URL = "https://newsapi.org/v2/everything"  # Example for NewsAPI.org


def get_news_articles(
    query: str,
    from_date: str = None,
    to_date: str = None,
    language: str = "en",
    sort_by: str = "relevancy",
    page_size: int = 10,
) -> list:
    """Fetches news articles based on a query.

    Args:
        query (str): The search query (e.g., stock symbol, company name).
        from_date (str, optional): A date and optional time for the oldest article allowed. Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS. Defaults to 7 days ago.
        to_date (str, optional): A date and optional time for the newest article allowed. Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS. Defaults to now.
        language (str): The 2-letter ISO-639-1 code of the language. Defaults to "en".
        sort_by (str): The order to sort the articles in. Defaults to "relevancy".
        page_size (int): The number of results to return per page. Defaults to 10.

    Returns:
        list: A list of dictionaries, where each dictionary represents a news article.
    """
    if not NEWS_API_KEY or NEWS_API_KEY == "YOUR_NEWS_API_KEY":
        print(
            "NEWS_API_KEY is not set. Please set it in your environment variables or replace the placeholder."
        )
        return []

    if from_date is None:
        from_date = (datetime.now() - timedelta(days=7)).isoformat()  # Last 7 days
    if to_date is None:
        to_date = datetime.now().isoformat()

    params = {
        "q": query,
        "from": from_date,
        "to": to_date,
        "language": language,
        "sortBy": sort_by,
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = requests.get(NEWS_API_BASE_URL, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data.get("articles", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news articles for query '{query}': {e}")
        return []
    except Exception as e:
        print(f"Error parsing news data: {e}")
        return []


if __name__ == "__main__":
    # Example Usage:
    print("\n--- Fetching news articles for Apple (AAPL) ---")
    aapl_news = get_news_articles("Apple Inc. OR AAPL", page_size=3)
    if aapl_news:
        for article in aapl_news:
            print(f"  Title: {article.get('title')}")
            print(f"  Source: {article.get('source', {}).get('name')}")
            print(f"  URL: {article.get('url')}\n")
    else:
        print("No news articles found for Apple.")

    print("\n--- Fetching news articles for Microsoft (MSFT) ---")
    msft_news = get_news_articles("Microsoft OR MSFT", page_size=2)
    if msft_news:
        for article in msft_news:
            print(f"  Title: {article.get('title')}")
            print(f"  Source: {article.get('source', {}).get('name')}")
            print(f"  URL: {article.get('url')}\n")
    else:
        print("No news articles found for Microsoft.")

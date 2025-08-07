# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the Flask app runs on
EXPOSE 5000

# Define environment variables (e.g., for API keys, database paths)
# It's better to pass these at runtime for production, but for development/testing
# you can set defaults here or use .env files with docker-compose.
ENV GOOGLE_SHEET_ID="YOUR_GOOGLE_SHEET_ID"
ENV ALPHA_VANTAGE_API_KEY="YOUR_ALPHA_VANTAGE_API_KEY"
ENV GMAIL_APP_PASSWORD="YOUR_GMAIL_APP_PASSWORD"
ENV GMAIL_USERNAME="YOUR_GMAIL_USERNAME"

# Run the Flask application when the container starts
# Use a production-ready WSGI server like Gunicorn instead of Flask's built-in server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "src.investor_intelligence.web_app.app:app"]
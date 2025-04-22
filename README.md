# Telegram Client

A desktop application for managing multiple Telegram accounts and sending messages via API.

## Project Structure

```
TelegramClient/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── views/
│   │   ├── __init__.py
│   │   └── main_window.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── api_controller.py
│   └── utils/
│       ├── __init__.py
│       └── logger_config.py
├── config/
├── logs/
├── build.spec
├── build.bat
├── setup.bat
├── requirements.txt     # List of dependencies
├── .env                 # Environment variables
├── README.md            # Project documentation
└── .gitignore           # Git ignore file
```

## Installation

1. Make sure Python 3.9+ is installed on your system
2. Extract all files from TelegramClient.zip
3. Run TelegramClient.bat
4. First run will create example configuration

## Configuration

1. Get your API credentials from <https://my.telegram.org/apps>
2. Add your credentials in the application interface
3. Click "Save All" to store credentials
4. Click "Start API" to begin the service

## Usage

The API server runs on <http://localhost:5000>

Send messages using:

```bash
POST /send-message
{
    "phone": "+84123456789",
    "destination": "@username",
    "message": "Hello world"
}
```

## Requirements

- Windows 7/10/11
- No additional software required
- Internet connection

@echo off
echo Building Python package...
python compile.py

echo Creating distribution archive...
powershell Compress-Archive -Path dist\TelegramClient -DestinationPath TelegramClient.zip -Force

echo Build complete! Distribution package is in TelegramClient.zip
pause
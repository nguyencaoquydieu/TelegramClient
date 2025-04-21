@echo off
echo Installing requirements...
pip install -r requirements.txt

echo Cleaning previous builds...
rmdir /s /q build dist
if exist TelegramClient.zip del TelegramClient.zip

echo Building application...
pyinstaller --clean build.spec

echo Creating distribution package...
powershell Compress-Archive -Path dist\TelegramClient -DestinationPath TelegramClient.zip -Force

echo Build complete! Distribution package is in TelegramClient.zip
pause
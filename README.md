# Real-Time Currency Converter

A production-style Python currency converter with a modern `CustomTkinter` desktop UI, synchronized terminal output, live exchange-rate fetching, cached offline fallback, favorites, history, CSV export, and theme settings.

For a full project explanation, usage guide, architecture summary, and feature walkthrough, see `PROJECT_GUIDE.md`.

## Features

- Live currency conversion with fresh rates on every request
- Terminal output and desktop GUI kept in sync
- Dynamic currency list loaded from the API
- Searchable currency pickers
- Swap, clear, copy, and keyboard shortcuts
- Conversion history with quick reuse
- Favorite currencies
- Auto-refresh support
- Dark and light theme toggle
- Cached offline fallback when live requests fail
- Export conversion history to CSV
- Responsive, non-blocking GUI using background threads

## Project Structure

```text
currency converter/
├── api/
│   ├── __init__.py
│   └── exchange_service.py
├── assets/
│   ├── logo.png
│   └── icons/
│       └── app.ico
├── data/
│   ├── exports/
│   ├── history.json
│   ├── logs/
│   ├── rates_cache.json
│   └── settings.json
├── gui/
│   ├── __init__.py
│   ├── app.py
│   ├── components.py
│   └── styles.py
├── models/
│   ├── __init__.py
│   ├── conversion.py
│   ├── currency.py
│   └── settings.py
├── services/
│   ├── __init__.py
│   ├── cache_service.py
│   ├── converter_service.py
│   └── settings_service.py
├── utils/
│   ├── __init__.py
│   ├── formatters.py
│   ├── logger.py
│   └── validators.py
├── config.py
├── main.py
├── README.md
└── requirements.txt
```

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer
- Internet connection for live exchange rates

## Install

### 1. Create and activate a virtual environment

On Windows PowerShell:

```powershell
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
```

If `py -3.10` is not available, replace it with your installed Python command.

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

## Run the Project

### Launch the desktop application

```powershell
py -3.10 main.py
```

### Run a CLI-only conversion

```powershell
py -3.10 main.py --cli-only --amount 100 --from-currency USD --to-currency INR
```

## How the App Works

1. The app loads available currencies from the exchange service.
2. Every conversion requests a fresh live rate.
3. If the live provider fails, the app falls back to a public backup provider.
4. If the network is unavailable but a cached rate exists, the app uses the cached rate.
5. Every successful conversion:
   - updates the GUI
   - prints the formatted result in the terminal
   - saves the result to history
   - updates the local rate cache

## Current API Strategy

The app is configured to try `ExchangeRate.host` first. If that provider rejects requests because an access key is required, the app automatically falls back to `Frankfurter`, which is currently public and reliable for no-key usage.

If you have an `ExchangeRate.host` access key, set it before running the app:

```powershell
$env:EXCHANGERATE_HOST_ACCESS_KEY="your_access_key"
py -3.10 main.py
```

## GUI Usage

- Enter an amount
- Choose source and target currencies
- Click `Convert` or press `Enter`
- Click `Swap` to reverse the pair
- Click `Copy` to copy the converted amount
- Click `Clear` to reset the form
- Use `Settings` to change refresh interval and favorites
- Use the history panel to reuse a previous conversion

## Keyboard Shortcuts

- `Enter` converts
- `Ctrl+S` swaps currencies
- `Ctrl+L` clears the form
- `Ctrl+C` copies the latest converted amount

## Data Files

The app creates and maintains these files automatically:

- `data/rates_cache.json`: cached exchange rates
- `data/history.json`: conversion history
- `data/settings.json`: saved theme, favorites, and refresh settings
- `data/exports/*.csv`: exported history files
- `data/logs/app.log`: application logs

## Offline Mode

Offline mode is supported through the local cache:

- If a live request fails and a cached rate exists for the same pair, the app uses the cached rate.
- If no cached rate exists yet, the app shows a friendly error message instead of crashing.

For best offline behavior, run at least one successful online conversion for the currency pair you need.

## Packaging With PyInstaller

Install PyInstaller:

```powershell
pip install pyinstaller
```

Build the executable:

```powershell
pyinstaller --noconfirm --onefile --windowed --name CurrencyConverter --icon assets/icons/app.ico --add-data "assets;assets" main.py
```

After the build finishes, the executable will be created in the `dist/` directory.

## Notes

- The desktop UI uses background threads so the window stays responsive during API calls.
- Currency values are calculated with `Decimal` to avoid floating-point precision issues.
- Terminal output is generated from the same conversion result object used by the GUI.

## Troubleshooting

### Python command not found

Try one of these:

```powershell
py -3.10 main.py
```

or

```powershell
python main.py
```

depending on your local Python installation.

### API request fails

- Check your internet connection
- Retry after a few seconds
- If `ExchangeRate.host` requires a key, rely on the built-in fallback or set `EXCHANGERATE_HOST_ACCESS_KEY`

### GUI does not open

Make sure `customtkinter`, `Pillow`, and `requests` are installed:

```powershell
pip install -r requirements.txt
```

# Project Guide

## Overview

`Real-Time Currency Converter` is a Python desktop and terminal currency conversion application.

It is built to:

- fetch live exchange rates from public APIs
- convert currencies in real time
- show results in both the GUI and terminal
- keep the UI responsive during network requests
- store cached data for offline fallback
- keep user settings and conversion history locally

The project uses a clean modular structure so the UI, business logic, API layer, and utilities stay separated and easy to maintain.

## What This Project Can Do

The application supports the following:

- live currency conversion
- desktop GUI using `CustomTkinter`
- terminal output for every conversion
- dynamic currency loading from API
- searchable currency selection
- source/target currency swapping
- copy converted amount
- clear current form
- theme toggle between light and dark mode
- conversion history
- favorite currencies
- auto-refresh settings
- CSV export of conversion history
- offline fallback using cached rates
- logging for troubleshooting

## Main Technologies Used

### Python

The application is written in Python and organized using object-oriented design.

### CustomTkinter

Used to build the modern desktop interface with a cleaner look than standard Tkinter.

### Requests

Used to call the exchange-rate APIs and retrieve live data.

### Pillow

Used for working with image assets such as the logo and icon.

### Threading

Used to run API calls in the background so the GUI does not freeze during network requests.

### Decimal

Used for accurate currency calculations instead of floating-point arithmetic.

## API Behavior

The project is designed to request a fresh live rate each time a conversion is made.

### Primary API

- `ExchangeRate.host`

### Fallback API

- `Frankfurter`

Why there is a fallback:

- `ExchangeRate.host` may require an access key in some environments
- to keep the project working reliably, the app automatically falls back to `Frankfurter`

### Offline Fallback

If both live providers fail but a cached rate exists for the same currency pair, the app uses the cached value instead of crashing.

## How the Project Works

The project flow is:

1. User enters amount and selects currencies.
2. The GUI sends the request to the conversion service.
3. The conversion service validates the input.
4. The exchange service requests the latest live rate.
5. If the primary provider fails, the backup provider is used.
6. If the network fails and cache exists, cached data is used.
7. The converted result is returned.
8. The GUI updates the result card and status.
9. The same result is printed in the terminal.
10. The result is saved to history and cache.

## Folder Structure

```text
currency converter/
├── api/
│   └── exchange_service.py
├── assets/
│   ├── logo.png
│   └── icons/app.ico
├── data/
│   ├── exports/
│   ├── history.json
│   ├── logs/app.log
│   ├── rates_cache.json
│   └── settings.json
├── gui/
│   ├── app.py
│   ├── components.py
│   └── styles.py
├── models/
│   ├── conversion.py
│   ├── currency.py
│   └── settings.py
├── services/
│   ├── cache_service.py
│   ├── converter_service.py
│   └── settings_service.py
├── utils/
│   ├── formatters.py
│   ├── logger.py
│   └── validators.py
├── config.py
├── main.py
├── PROJECT_GUIDE.md
├── README.md
└── requirements.txt
```

## File Responsibilities

### `main.py`

Application entry point.

It:

- creates services
- launches the GUI
- also supports CLI-only execution

### `config.py`

Stores project constants such as:

- app name
- default currencies
- file paths
- API URLs
- timeout values

### `api/exchange_service.py`

Handles:

- currency list loading
- live rate fetching
- provider fallback
- API error handling

### `services/converter_service.py`

This is the main business logic layer.

It:

- performs conversion flow
- coordinates validation
- calls the exchange service
- stores history
- prints synchronized terminal output

### `services/cache_service.py`

Handles local JSON storage for:

- cached rates
- conversion history
- CSV export

### `services/settings_service.py`

Handles local settings storage for:

- theme
- favorites
- refresh interval
- default currencies

### `gui/app.py`

Contains the main desktop application window and GUI event handling.

### `gui/components.py`

Contains reusable user interface components such as:

- searchable currency picker
- result card
- status bar
- history panel

### `gui/styles.py`

Contains theme colors and UI style values.

### `utils/validators.py`

Validates amount and currency inputs.

### `utils/formatters.py`

Formats:

- amounts
- timestamps
- terminal output text

### `utils/logger.py`

Configures logging to file and console.

## Running the Project

## 1. Create virtual environment

```powershell
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
```

## 2. Install dependencies

```powershell
pip install -r requirements.txt
```

## 3. Launch the desktop application

```powershell
py -3.10 main.py
```

## 4. Run CLI mode

```powershell
py -3.10 main.py --cli-only --amount 100 --from-currency USD --to-currency INR
```

## GUI Features Explained

### Amount Input

The user enters the value to convert.

### From Currency / To Currency

The user selects the currency pair. The list is loaded from the API and is searchable.

### Convert Button

Fetches the latest live rate and shows the conversion result.

### Swap Button

Reverses source and target currencies quickly.

### Clear Button

Resets the form and output fields.

### Copy Button

Copies the latest converted value to the clipboard.

### Settings Button

Opens a settings window to manage:

- auto-refresh
- refresh interval
- favorites

### Theme Toggle

Switches between light and dark appearance.

### History Panel

Displays recent conversions and allows reusing them.

## Terminal Output

Every conversion also prints a formatted block in the terminal so GUI and CLI outputs stay synchronized.

Example:

```text
------------------------------------
Currency Converter
------------------------------------

Amount:
100.00

From:
USD

To:
INR

Exchange Rate:
1 USD = 95.4000 INR

Converted Amount:
₹9,540.00

Time:
2026-07-07 15:10:11
------------------------------------
```

## Saved Local Data

The application automatically creates the following files:

- `data/rates_cache.json`
- `data/history.json`
- `data/settings.json`
- `data/exports/*.csv`
- `data/logs/app.log`

## Error Handling

The project handles:

- empty amount
- invalid number input
- zero or negative amount
- invalid currencies
- API failures
- timeout issues
- no internet connection
- missing cached data
- unexpected runtime exceptions

Instead of crashing, the app shows user-friendly messages.

## Performance Design

The project is designed to stay responsive by:

- performing API calls in background threads
- separating UI code from business logic
- caching previous rates
- saving data locally in lightweight JSON files

## Packaging

To build a Windows executable:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name CurrencyConverter --icon assets/icons/app.ico --add-data "assets;assets" main.py
```

The built application will be created in the `dist/` folder.

## Limitations and Notes

- offline mode only works for currency pairs that were previously fetched successfully
- live rates depend on external APIs
- the project currently uses a fallback provider because `ExchangeRate.host` may require an access key

## Recommended Improvements

Possible future improvements:

- add automated unit tests
- add more advanced settings
- improve search popup theme styling further
- add multi-language support
- add installer packaging

## Quick Start Summary

If you only want the shortest path:

```powershell
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py -3.10 main.py
```

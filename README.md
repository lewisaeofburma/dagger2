# Football Analysis App

A Python application for scraping and analyzing Premier League football data from FBRef.com.

## Features

- Scrapes Premier League team data
- Retrieves league standings and statistics
- Saves data in organized JSON files
- Takes screenshots for debugging
- Comprehensive error handling and logging

## Project Structure

```
football_analysis/
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── teams_scraper.py
│   │   └── league_stats_scraper.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── file_manager.py
├── data/
│   ├── teams/
│   ├── standings/
│   └── stats/
├── logs/
├── debug/
│   └── screenshots/
├── tests/
├── requirements.txt
├── README.md
└── main.py
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   ```bash
   # On macOS/Linux:
   source .venv/bin/activate
   
   # On Windows:
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main script:
```bash
python main.py
```

This will:
1. Fetch Premier League teams
2. Get current league standings
3. Retrieve team statistics
4. Save all data in JSON format
5. Generate logs and screenshots (if errors occur)

## Data Organization

- `/data/teams/`: Team information and URLs
- `/data/standings/`: League standings with points and records
- `/data/stats/`: Detailed team statistics
- `/logs/`: Application logs with rotation
- `/debug/screenshots/`: Error screenshots for debugging

## Error Handling

The app includes comprehensive error handling:
- Screenshots are taken when errors occur
- Detailed logs are saved with timestamps
- Backups are created before overwriting data files
- Graceful handling of missing data

## Dependencies

- selenium: Web scraping with browser automation
- webdriver-manager: Chrome WebDriver management
- beautifulsoup4: HTML parsing (when needed)
- lxml: Fast HTML parsing

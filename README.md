# Football Data Analysis Application

A Python application for scraping, analyzing, and visualizing football (soccer) statistics from fbref.com.

## Features

- Scrape Premier League team information and statistics
- Collect detailed player statistics for teams
- Fetch league standings and team performance metrics
- Process and analyze football data
- Visualize team and player performance

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
dagger2/
├── data/                  # Stored JSON data (teams, standings)
├── debug/                 # Debugging utilities
│   └── output/            # Debug output files
├── logs/                  # Application logs
├── src/                   # Main source code
│   ├── config/            # Configuration system
│   ├── data_preparation/  # Data processing modules
│   ├── scrapers/          # Web scraping modules (legacy)
│   ├── services/          # Business logic services
│   ├── utils/             # Utility functions
│   └── visualizers/       # Data visualization
└── tests/                 # Test directory
    └── fixtures/          # Test fixtures
```

### Key Components

- **Configuration System**: Centralized configuration management
- **Service Layer**: Business logic separated from data access
- **WebDriver Pool**: Efficient management of WebDriver instances
- **Rate Limiter**: Prevents IP blocking by limiting request frequency
- **Data Processing**: Transforms raw data into analysis-ready formats
- **Visualization**: Creates visual representations of the data

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/dagger2.git
   cd dagger2
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Chrome and ChromeDriver (required for web scraping):
   - Chrome: https://www.google.com/chrome/
   - ChromeDriver: https://sites.google.com/chromium.org/driver/

## Usage

### Basic Usage

Run the main application:

```bash
python src/main.py
```

This will fetch Premier League teams, standings, and detailed statistics for all teams.

### Command Line Options

The application supports several command line options:

```bash
python src/main.py --team "Liverpool"  # Analyze a specific team
python src/main.py --standings         # Fetch league standings
python src/main.py --debug             # Enable debug mode
python src/main.py --headless          # Run in headless mode
```

### Configuration

You can customize the application behavior by modifying the configuration in `src/config/config.py` or by creating a `config.json` file in the project root.

Example configuration:

```json
{
  "teams_to_analyze": ["Liverpool", "Arsenal", "Manchester City"],
  "webdriver_settings": {
    "headless": true
  },
  "rate_limit_requests": 5,
  "rate_limit_period": 60
}
```

## Development

### Running Tests

Run the unit tests:

```bash
python -m unittest discover tests
```

### Project Structure

- **src/config/**: Configuration management
- **src/services/**: Business logic services
- **src/utils/**: Utility functions and helpers
- **src/data_preparation/**: Data processing and transformation
- **src/visualizers/**: Data visualization components
- **debug/**: Debugging tools and utilities
- **tests/**: Unit and integration tests

## Security Considerations

- The application implements rate limiting to avoid IP blocking
- Selenium stealth mode is used to avoid detection as a bot
- Error handling is implemented to handle network issues and site changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [FBRef](https://fbref.com/) for providing the football statistics data
- [Selenium](https://www.selenium.dev/) for web automation
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [Pandas](https://pandas.pydata.org/) for data manipulation
- [Matplotlib](https://matplotlib.org/) and [Seaborn](https://seaborn.pydata.org/) for visualization

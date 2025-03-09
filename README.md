# DeFi Sentinel

DeFi Sentinel is an agent that evaluates DeFi projects using various data sources, AI-based risk assessments, and provides assessment for tokens held on Sonic. It allows evaluation of projects, retrieval of token data, and reports generation in an efficient manner. The application is built with Flask and uses MongoDB to store project reports.

## Directory Structure

```
assessment
    ├── agent_choice.py        # Logic to evaluate projects on Sonic
    └── user_tokens.py         # Logic to fetch and evaluate tokens in user wallet
core
    ├── fetch_audits_hacks.py  # Fetch audit/security score and hack data
    ├── fetch_cmc_data.py     # Fetch CoinMarketCap data
    ├── fetch_tvl.py          # Fetch TVL and DeFi-related metrics
    └── fetch_user_tokens.py  # Fetch user's token data from sources
scripts
    ├── push_report_to_db.py  # One-time logic to push project data and AI reports to MongoDB
    └── sonic_tvl_to_db.py    # Logic for pushing TVL data related to Sonic projects
static
    └── (Static files)        # Static assets (CSS, JS, images)
templates
    └── (HTML files)          # Flask templates for rendering reports
utils
    ├── db_client.py          # MongoDB client connection logic
    ├── rate_limiters.py      # Rate limiting logic to avoid abuse
    
.env                          # Environment variables (API keys, DB credentials) add your own
app.py                        # Main Flask application file
Procfile                      # Heroku deployment configuration
```

## Overview

### Core Components

- **Core**: This directory contains the logic to fetch essential data for evaluating DeFi projects, including audit/security scores, hack history, TVL, and other metrics.
    - `fetch_audits_hacks.py`: Fetches audit/security scores and hack data from various sources.
    - `fetch_cmc_data.py`: Fetches data related to CoinMarketCap (CMCs), such as market prices and rankings.
    - `fetch_tvl.py`: Fetches TVL (Total Value Locked) and other DeFi metrics.
    - `fetch_user_tokens.py`: Fetches details of tokens in a user's wallet.

### Scripts

- **Scripts**: These are used to push data from various sources to MongoDB. These scripts handle one-time operations to optimize the application’s data retrieval process.
    - `push_report_to_db.py`: A script to push generated reports and project data to MongoDB.
    - `sonic_tvl_to_db.py`: A script for pushing TVL data related to Sonic projects into MongoDB.

### Assessment

- **Assessment**: This module contains logic for project evaluations.
    - `agent_choice.py`: This script is used for evaluating DeFi projects on Sonic and other dynamic tokens.
    - `user_tokens.py`: This script dynamically fetches user tokens and evaluates them based on their current status and risk.

### Utilities

- **Utils**: This folder includes utility files for connecting to MongoDB and handling rate limiting.
    - `db_client.py`: MongoDB client configuration and connection logic.
    - `rate_limiters.py`: Implements rate-limit functionality to avoid abuse of the system.

### Static and Templates

- **Static**: Contains CSS, JavaScript, and image files used to style the application’s web pages.
- **Templates**: Contains HTML templates used by the Flask app to render reports and other data.

## How to Run

1. Clone the repository:

   ```bash
   git clone https://github.com/AuditoneCodebase/Defi-Sentinel
   cd Defi-Sentinel
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in the `.env` file:
   - `MONGO_URI`: MongoDB connection string.
   - `OPENAI_API_KEY`: API key for OpenAI.
   - `SONIC_API_KEY`: API key from Sonic explorer developer dashboard

4. Run the Flask application:

   ```bash
   python app.py
   ```

5. The application will be available at `http://127.0.0.1:5000` by default.

## Contributions

We welcome contributions to improve the application. Here are ways you can help:
- Add new data sources for evaluating DeFi projects.
- Improve the rate limiting logic to handle more requests efficiently.
- Implement more evaluation criteria for projects.

If you would like to contribute, please fork the repo, make your changes, and create a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

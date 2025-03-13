# Business Contact Scraper

A Python tool to collect business contact information (emails and phone numbers) from company websites in regions where the local time is currently within business hours (7 AM to 2 PM).

## Features

- Automatically determines which regions are currently in business hours
- Prioritizes English-speaking regions
- Searches for company websites in the active regions
- Extracts email addresses and phone numbers from websites
- Logs all discovered contact information to a file
- Provides summary statistics on the scraping process

## Requirements

- Python 3.6+
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/business-scraper.git
   cd business-scraper
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the script with default settings:

```
python scraper.py
```

The script will:
1. Find regions where the current time is between 7 AM and 2 PM
2. Search for companies in those regions, starting with England
3. Visit company websites and extract contact information
4. Log the discovered contact information to `business_contacts_log.txt`

## Customization

You can modify the script parameters in the main function call:

```python
collect_business_contacts(
    num_results=10,  # Number of search results to process per region
    max_contacts=100,  # Maximum number of contacts to collect
    english_only=True  # Whether to limit searches to English-speaking regions
)
```

## Output

The script generates a log file (`business_contacts_log.txt`) with the following format:

```
# Business Contact Information - Generated YYYY-MM-DD HH:MM:SS UTC
# Format: Timestamp - Website URL (Location) | Email: email@example.com | Phone: phone_number

2023-03-12 14:23:45 UTC - https://example.com (Location: England) | Email: contact@example.com | Phone: +1 234 567 8901
```

## License

MIT 
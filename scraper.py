import requests
from googlesearch import search
import pytz
from datetime import datetime
import re
from bs4 import BeautifulSoup
import os
import random

LOG_FILE = "business_contacts_log.txt"

# Updated list of primarily English-speaking regions with accurate categorization
ENGLISH_SPEAKING_REGIONS = [
    # Primary English-speaking countries
    # UK and Ireland
    "Europe/London",  # England, Scotland, Wales
    "Europe/Dublin",  # Ireland
    
    # North America
    "America/New_York",  # Eastern US
    "America/Chicago",   # Central US
    "America/Denver",    # Mountain US
    "America/Los_Angeles",  # Western US
    "America/Toronto",   # Eastern Canada
    "America/Winnipeg",  # Central Canada
    "America/Edmonton",  # Mountain Canada
    "America/Vancouver", # Western Canada
    
    # Australia & New Zealand
    "Australia/Sydney",  # Eastern Australia
    "Australia/Adelaide", # Central Australia
    "Australia/Perth",   # Western Australia
    "Pacific/Auckland",  # New Zealand
    
    # Caribbean (English as official language)
    "America/Jamaica",   # Jamaica
    "America/Barbados",  # Barbados
    "America/Nassau",    # Bahamas
    "America/Port_of_Spain", # Trinidad and Tobago
    
    # Africa (English as official language)
    "Africa/Johannesburg", # South Africa
    "Africa/Lagos",      # Nigeria
    "Africa/Nairobi",    # Kenya
    "Africa/Accra",      # Ghana
    
    # Asia (regions with significant English business usage)
    "Asia/Singapore",    # Singapore (English is one of four official languages)
    "Asia/Hong_Kong",    # Hong Kong (English is one of two official languages)
    "Asia/Manila",       # Philippines (English is one of two official languages)
    
    # Secondary English-speaking business hubs
    # Countries where English is widely used in international business
    "Europe/Amsterdam",  # Netherlands
    "Europe/Stockholm",  # Sweden
    "Europe/Oslo",       # Norway
    "Europe/Copenhagen", # Denmark
    "Europe/Berlin",     # Germany
    "Europe/Zurich",     # Switzerland
    "Asia/Dubai",        # UAE
]

def get_time_zones_in_range(start_hour=7, end_hour=14, english_only=True):
    """Returns a list of time zones where the local time is within the given range."""
    valid_time_zones = []
    current_utc_time = datetime.utcnow()
    
    # Get all time zones or just English speaking ones
    time_zones_to_check = ENGLISH_SPEAKING_REGIONS if english_only else pytz.all_timezones
    
    print(f"Checking time zones between {start_hour}:00 and {end_hour}:00 local time...")
    
    for tz in time_zones_to_check:
        try:
            # Get current time in this timezone
            local_time = datetime.now(pytz.timezone(tz))
            local_hour = local_time.hour
            
            if start_hour <= local_hour <= end_hour:
                valid_time_zones.append(tz)
                print(f"✓ {tz}: Current time is {local_time.strftime('%H:%M')} - Within business hours")
            else:
                print(f"✗ {tz}: Current time is {local_time.strftime('%H:%M')} - Outside business hours")
        except Exception as e:
            # Skip any timezone that causes errors
            print(f"! Error with timezone {tz}: {str(e)}")
            continue
    
    return valid_time_zones

def get_company_websites(query, num_results=10):
    """Search Google for companies and return their website URLs."""
    websites = []
    try:
        for result in search(query, num=num_results, stop=num_results):
            websites.append(result)
    except Exception as e:
        print(f"Error fetching Google search results: {e}")
    return websites

def extract_contact_info(url):
    """Extract email addresses and phone numbers from a website."""
    email = None
    phone = None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text content
        text = soup.get_text()
        
        # Find emails using regex
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        if emails:
            # Filter out common false positives
            filtered_emails = [e for e in emails if not (e.endswith('.png') or e.endswith('.jpg') or e.endswith('.gif'))]
            if filtered_emails:
                email = filtered_emails[0]  # Take the first valid email found
        
        # Find phone numbers using regex (improved pattern)
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        if phones:
            phone = phones[0]  # Take the first phone found
                
    except Exception as e:
        print(f"Error extracting contact info from {url}: {str(e)}")
        
    return email, phone

def check_website_status(url):
    """Check website status."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            return "OK"
        else:
            return f"Error {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Connection Failed: {str(e)}"

def log_business_contact(url, location, email=None, phone=None):
    """Log business contact information to a file."""
    with open(LOG_FILE, "a") as file:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        contact_info = ""
        if email:
            contact_info += f" | Email: {email}"
        if phone:
            contact_info += f" | Phone: {phone}"
        
        if email or phone:  # Only log if we have either email or phone
            file.write(f"{timestamp} - {url} (Location: {location}){contact_info}\n")
            return True
        return False

def get_location_name(timezone):
    """Get a more user-friendly location name from a timezone."""
    # Mapping of timezones to more readable location names
    timezone_mapping = {
        "Europe/London": "United Kingdom",
        "Europe/Dublin": "Ireland",
        "America/New_York": "Eastern USA",
        "America/Chicago": "Central USA",
        "America/Denver": "Mountain USA",
        "America/Los_Angeles": "Western USA",
        "America/Toronto": "Eastern Canada",
        "America/Winnipeg": "Central Canada",
        "America/Edmonton": "Western Canada",
        "America/Vancouver": "Western Canada",
        "Australia/Sydney": "Eastern Australia",
        "Australia/Adelaide": "Central Australia",
        "Australia/Perth": "Western Australia",
        "Pacific/Auckland": "New Zealand",
        "America/Jamaica": "Jamaica",
        "America/Barbados": "Barbados",
        "America/Nassau": "Bahamas",
        "America/Port_of_Spain": "Trinidad and Tobago",
        "Africa/Johannesburg": "South Africa",
        "Africa/Lagos": "Nigeria",
        "Africa/Nairobi": "Kenya",
        "Africa/Accra": "Ghana",
        "Asia/Singapore": "Singapore",
        "Asia/Hong_Kong": "Hong Kong",
        "Asia/Manila": "Philippines",
        "Europe/Amsterdam": "Netherlands",
        "Europe/Stockholm": "Sweden",
        "Europe/Oslo": "Norway",
        "Europe/Copenhagen": "Denmark",
        "Europe/Berlin": "Germany",
        "Europe/Zurich": "Switzerland",
        "Asia/Dubai": "UAE",
    }
    
    # Check if we have a mapping for this timezone
    if timezone in timezone_mapping:
        return timezone_mapping[timezone]
    
    # Otherwise, fallback to the old method
    if '/' in timezone:
        location = timezone.split('/')[-1]
    else:
        location = timezone
        
    # Replace underscores with spaces
    location = location.replace('_', ' ')
    
    return location

def collect_business_contacts(num_results=10, max_contacts=100, english_only=True):
    """Collect contact information for businesses in time zones where local time is between 7 AM and 2 PM."""
    valid_time_zones = get_time_zones_in_range(english_only=english_only)
    
    if not valid_time_zones:
        print("No valid time zones found in the given range.")
        return []
    
    businesses_with_contacts = []
    total_companies_checked = 0
    
    print(f"\nChecking websites in {'English-speaking regions' if english_only else 'all regions'} where it's between 7 AM and 2 PM...")
    print(f"Will continue searching until collecting contact info for {max_contacts} businesses...")
    print(f"Found {len(valid_time_zones)} time zones in business hours: {', '.join(valid_time_zones)}")
    
    # Clear previous log file
    with open(LOG_FILE, "w") as file:
        file.write(f"# Business Contact Information - Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        file.write(f"# Format: Timestamp - Website URL (Location) | Email: email@example.com | Phone: phone_number\n\n")
    
    # Start by explicitly searching in UK first
    print(f"\nSearching for companies in the United Kingdom...")
    uk_search_query = "companies in United Kingdom"
    uk_websites = get_company_websites(uk_search_query, num_results*3)  # Get more results for UK
    
    for website in uk_websites:
        total_companies_checked += 1
        
        # Check if website is accessible
        status = check_website_status(website)
        
        # Extract contact information
        email, phone = extract_contact_info(website)
        
        if email or phone:
            print(f"✅ Contact found: {website} | Email: {email} | Phone: {phone}")
            if log_business_contact(website, "United Kingdom", email, phone):
                businesses_with_contacts.append((website, "United Kingdom", email, phone))
                print(f"Progress: Collected {len(businesses_with_contacts)} of {max_contacts} business contacts")
        else:
            print(f"❌ No contact info: {website} ({status})")
        
        if len(businesses_with_contacts) >= max_contacts:
            break
    
    # If we still need more contacts, continue with other regions
    if len(businesses_with_contacts) < max_contacts:
        # Then search through time zones
        for tz in valid_time_zones:
            if len(businesses_with_contacts) >= max_contacts:
                print(f"\nReached maximum of {max_contacts} business contacts collected. Stopping.")
                break
                
            location = get_location_name(tz)
            # Skip UK as we already searched there
            if location == "United Kingdom":
                continue
                
            search_query = f"companies in {location}"
            
            print(f"\nSearching for companies in {location}...")
            websites = get_company_websites(search_query, num_results)
            
            for website in websites:
                total_companies_checked += 1
                
                # Check if website is accessible
                status = check_website_status(website)
                
                # Extract contact information
                email, phone = extract_contact_info(website)
                
                if email or phone:
                    print(f"✅ Contact found: {website} | Email: {email} | Phone: {phone}")
                    if log_business_contact(website, location, email, phone):
                        businesses_with_contacts.append((website, location, email, phone))
                        print(f"Progress: Collected {len(businesses_with_contacts)} of {max_contacts} business contacts")
                else:
                    print(f"❌ No contact info: {website} ({status})")
                
                if len(businesses_with_contacts) >= max_contacts:
                    break

    print(f"\nTotal companies checked: {total_companies_checked}")
    print(f"Total business contacts collected: {len(businesses_with_contacts)}")
    
    if businesses_with_contacts:
        print("\nBusiness Contacts Collected:")
        for site, loc, email, phone in businesses_with_contacts:
            email_info = f" | Email: {email}" if email else ""
            phone_info = f" | Phone: {phone}" if phone else ""
            print(f"{site} (Location: {loc}){email_info}{phone_info}")
        print(f"\nResults have been logged to {LOG_FILE}")
    else:
        print("\nNo business contacts found.")
    
    return businesses_with_contacts

if __name__ == "__main__":
    collect_business_contacts(num_results=10, max_contacts=100, english_only=True) 
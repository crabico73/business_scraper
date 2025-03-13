import requests
from googlesearch import search
import pytz
from datetime import datetime
import re
from bs4 import BeautifulSoup
import os
import random
import time
import csv

# File to log broken websites with contact info
BROKEN_WEBSITES_LOG = "broken_websites_contacts.csv"
BROKEN_WEBSITES_SUMMARY = "broken_websites_summary.txt"

# Updated list to focus on small to medium companies in Singapore, Philippines, and Malaysia
COMPANY_SEARCH_QUERIES = [
    "small business Singapore",
    "medium enterprises Singapore",
    "SME Singapore",
    "small business Philippines",
    "medium enterprises Philippines", 
    "SME Philippines",
    "small business Malaysia",
    "medium enterprises Malaysia",
    "SME Malaysia",
    "startup companies Singapore",
    "startup companies Philippines",
    "startup companies Malaysia",
    "local business Singapore",
    "local business Philippines",
    "local business Malaysia"
]

def get_company_websites(num_results=20):
    """Get a list of small to medium company websites from Singapore, Philippines, and Malaysia"""
    all_websites = []
    
    for query in COMPANY_SEARCH_QUERIES:
        try:
            print(f"\nSearching for: {query}")
            results = []
            for result in search(query, num=num_results, stop=num_results, pause=3.0):
                results.append(result)
                print(f"Found: {result}")
                # Increased delay between searches to avoid rate limiting
                time.sleep(1.5)
                
            all_websites.extend(results)
            print(f"Found {len(results)} websites for query: {query}")
            
            # Take a longer break between queries to avoid rate limiting
            time.sleep(10)
                
        except Exception as e:
            print(f"Error searching for {query}: {e}")
            print("Waiting 60 seconds before continuing...")
            time.sleep(60)  # Wait longer if we hit an error
            
    print(f"\nTotal websites collected: {len(all_websites)}")
    return all_websites

def check_website_status(url):
    """Check if a website is broken and return status details"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
        
        # Consider 4xx and 5xx as broken
        if 400 <= response.status_code < 600:
            return {
                "status": "Broken", 
                "code": response.status_code, 
                "reason": response.reason
            }
        else:
            return {
                "status": "Working", 
                "code": response.status_code, 
                "reason": response.reason
            }
    except requests.exceptions.RequestException as e:
        # Connection errors, timeouts, etc.
        return {
            "status": "Broken", 
            "code": "Connection Error", 
            "reason": str(e)
        }

def extract_contact_info(url):
    """Extract contact information from a website or WHOIS data"""
    email = None
    phone = None
    company_name = None
    
    # First try to get the company name from the URL
    url_parts = url.replace("http://", "").replace("https://", "").split("/")[0].split(".")
    if len(url_parts) >= 2:
        company_name = url_parts[-2].capitalize()  # Use domain name as company name
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try to access the site even if broken - sometimes we can still get the HTML
        try:
            response = requests.get(url, timeout=10, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to extract company name from title if available
            if soup.title and soup.title.string:
                company_name = soup.title.string.strip()
                # Clean up common title patterns
                company_name = re.sub(r' - Home$| - Official Website$| - Official Site$', '', company_name)
                company_name = re.sub(r' \| .*$', '', company_name)
            
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
                
            # Try to look specifically in contact-related pages if we didn't find info
            if not email or not phone:
                contact_links = []
                for link in soup.find_all('a', href=True):
                    href = link['href'].lower()
                    if 'contact' in href or 'about' in href:
                        if href.startswith('http'):
                            contact_links.append(href)
                        elif href.startswith('/'):
                            # Handle relative URLs
                            base_url = '/'.join(url.split('/')[:3])  # Get domain part
                            contact_links.append(base_url + href)
                
                # Visit up to 2 contact-related pages
                for contact_url in contact_links[:2]:
                    try:
                        contact_response = requests.get(contact_url, timeout=5, headers=headers)
                        contact_soup = BeautifulSoup(contact_response.text, 'html.parser')
                        contact_text = contact_soup.get_text()
                        
                        # Look for email
                        if not email:
                            contact_emails = re.findall(email_pattern, contact_text)
                            filtered_contact_emails = [e for e in contact_emails if not (e.endswith('.png') or e.endswith('.jpg') or e.endswith('.gif'))]
                            if filtered_contact_emails:
                                email = filtered_contact_emails[0]
                                
                        # Look for phone
                        if not phone:
                            contact_phones = re.findall(phone_pattern, contact_text)
                            if contact_phones:
                                phone = contact_phones[0]
                                
                        # If we found both, we can stop
                        if email and phone:
                            break
                    except:
                        continue
        except:
            # If we can't access the site, we'll try other methods
            pass
            
    except Exception as e:
        print(f"Error extracting contact info from {url}: {str(e)}")
    
    return {
        "company_name": company_name,
        "email": email,
        "phone": phone
    }

def log_broken_website(url, status, contact_info):
    """Log broken website information to a CSV file"""
    file_exists = os.path.isfile(BROKEN_WEBSITES_LOG)
    
    with open(BROKEN_WEBSITES_LOG, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['URL', 'Company', 'Status Code', 'Reason', 'Email', 'Phone', 'Timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'URL': url,
            'Company': contact_info["company_name"] if contact_info["company_name"] else "Unknown",
            'Status Code': status["code"],
            'Reason': status["reason"],
            'Email': contact_info["email"] if contact_info["email"] else "Not found",
            'Phone': contact_info["phone"] if contact_info["phone"] else "Not found",
            'Timestamp': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        })

def create_summary(broken_websites):
    """Create a summary of broken websites with contact information"""
    with open(BROKEN_WEBSITES_SUMMARY, 'w', encoding='utf-8') as f:
        f.write(f"# Broken Websites Summary - Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        
        f.write(f"Total websites checked: {broken_websites['total_checked']}\n")
        f.write(f"Total broken websites found: {broken_websites['total_broken']}\n")
        f.write(f"Broken websites with contact information: {broken_websites['with_contact']}\n\n")
        
        f.write("## Broken Websites with Contact Information\n\n")
        
        for website in broken_websites['websites']:
            f.write(f"### {website['company_name'] if website['company_name'] else 'Unknown Company'}\n")
            f.write(f"- URL: {website['url']}\n")
            f.write(f"- Status: {website['status']['code']} {website['status']['reason']}\n")
            
            if website['contact_info']['email']:
                f.write(f"- Email: {website['contact_info']['email']}\n")
            else:
                f.write("- Email: Not found\n")
                
            if website['contact_info']['phone']:
                f.write(f"- Phone: {website['contact_info']['phone']}\n")
            else:
                f.write("- Phone: Not found\n")
                
            f.write("\n")

def find_broken_websites_with_contacts(max_websites=100, max_contacts=15):
    """Find broken websites and collect their contact information"""
    print(f"Collecting company websites... This may take some time.")
    
    # Initialize empty CSV file
    with open(BROKEN_WEBSITES_LOG, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['URL', 'Company', 'Status Code', 'Reason', 'Email', 'Phone', 'Timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    
    # Get company websites
    websites = get_company_websites(num_results=20)
    
    # Check website status and collect contact information
    broken_websites_data = {
        'total_checked': 0,
        'total_broken': 0,
        'with_contact': 0,
        'websites': []
    }
    
    print("\nChecking website status and collecting contact information...")
    
    # Shuffle the websites list to get a random sample
    random.shuffle(websites)
    
    for url in websites[:max_websites]:
        broken_websites_data['total_checked'] += 1
        
        print(f"\nChecking: {url}")
        status = check_website_status(url)
        
        if status["status"] == "Broken":
            broken_websites_data['total_broken'] += 1
            print(f"❌ Broken website found: {url} - {status['code']} {status['reason']}")
            
            # Extract contact information
            print(f"Attempting to extract contact information...")
            contact_info = extract_contact_info(url)
            
            if contact_info["email"] or contact_info["phone"]:
                broken_websites_data['with_contact'] += 1
                print(f"✅ Contact information found!")
                if contact_info["email"]:
                    print(f"   Email: {contact_info['email']}")
                if contact_info["phone"]:
                    print(f"   Phone: {contact_info['phone']}")
                
                # Log to CSV
                log_broken_website(url, status, contact_info)
                
                # Add to list for summary
                broken_websites_data['websites'].append({
                    'url': url,
                    'company_name': contact_info["company_name"],
                    'status': status,
                    'contact_info': contact_info
                })
                
                # Stop if we've collected enough contacts
                if broken_websites_data['with_contact'] >= max_contacts:
                    print(f"\nReached the maximum of {max_contacts} broken websites with contact information. Stopping.")
                    break
            else:
                print(f"❌ No contact information found.")
        else:
            print(f"✓ Website working: {url} - {status['code']} {status['reason']}")
        
        # Small delay between checks
        time.sleep(1)
    
    # Create summary
    create_summary(broken_websites_data)
    
    # Print summary
    print("\n--- SUMMARY ---")
    print(f"Total websites checked: {broken_websites_data['total_checked']}")
    print(f"Total broken websites found: {broken_websites_data['total_broken']}")
    print(f"Broken websites with contact information: {broken_websites_data['with_contact']}")
    
    if broken_websites_data['with_contact'] > 0:
        print(f"\nResults have been saved to {BROKEN_WEBSITES_LOG} and {BROKEN_WEBSITES_SUMMARY}")
    else:
        print("\nNo broken websites with contact information found.")
    
    return broken_websites_data

if __name__ == "__main__":
    print("Starting broken website collector for small to medium companies in Southeast Asia...")
    print("This script will:")
    print("1. Search for small to medium businesses in Singapore, Philippines, and Malaysia")
    print("2. Check if the websites are broken")
    print("3. Extract contact information from broken websites")
    print("4. Stop after collecting information for 15 companies")
    
    # Start the search
    find_broken_websites_with_contacts(max_websites=200, max_contacts=15) 
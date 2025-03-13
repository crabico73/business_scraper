import scraper

if __name__ == "__main__":
    print("Running test version of the business scraper...")
    print("This will collect a maximum of 5 business contacts for testing purposes.")
    
    # Run with limited results to test functionality
    scraper.collect_business_contacts(
        num_results=2,     # Only 2 search results per region to speed up testing
        max_contacts=5,    # Only collect 5 contacts in total
        english_only=True  # Still limit to English-speaking regions
    ) 
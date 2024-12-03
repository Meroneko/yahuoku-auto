from selenium import webdriver

def run_script(config):
    # Initialize the browser with the specified profile
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={config['browser_profile_path']}")
    driver = webdriver.Chrome(options=options)
    
    try:
        # Example: Open Yahoo Auction
        driver.get("https://auctions.yahoo.co.jp/")
        # Add your selenium script logic here
    finally:
        driver.quit()

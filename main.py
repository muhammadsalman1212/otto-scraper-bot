import csv
import json
import time
import random
from playwright.sync_api import sync_playwright

csv_name = input("Enter the name of the CSV file: ")



# Link to the page being scraped
link = 'https://www.otto.de/babys/ausstattung/babyphone/?reduziert'

with sync_playwright() as p:
    browser = p.firefox.launch_persistent_context(user_data_dir="userDir", headless=False)
    page = browser.new_page()
    page.goto(link, timeout=0)

    # Accept cookies
    try:
        page.locator('//button[@id="onetrust-accept-btn-handler"]').click(timeout=5000)
    except:
        pass

    product_links = []
    count = 120

    # Loop to scroll and collect product links
    while True:
        updated_link = f'{link}&l=gq&o={count}'
        page.goto(updated_link, timeout=0)
        current_url = page.url

        if current_url == link:
            break

        # Scroll to load more products
        for _ in range(32):
            page.mouse.wheel(0, random.randint(1000, 1200))
            time.sleep(random.uniform(0.5, 1))

        # Scrape product links
        links = page.locator('//header[@class="find_tile__header"]//a[@class="find_tile__productLink"]')
        for i in range(links.count()):
            href = links.nth(i).get_attribute('href')
            product_links.append(f"https://www.otto.de{href}")

        print(product_links)
        count += 120

    # Process each product link
    total_links = len(product_links)
    processed_count = 1

    for product_link in product_links:
        try:
            page.goto(product_link, timeout=0)
            time.sleep(2)

            # Extract product data from page
            script_content = page.evaluate('''() => {
                return document.getElementById("product_data_json").innerHTML;
            }''')
            product_data = json.loads(script_content)

            # Extract GTIN and Price
            gtin = product_data.get("gtin13")
            price = product_data["offers"]["price"]
            print(f"GTIN13: {gtin}")
            print(f"Price: {price} EUR")
            print(f"{processed_count}/{total_links}")

        except Exception as e:
            print(f"Error processing {product_link}: {e}")
            gtin = "Not Found"
            price = "Not Found"

        # Write data to CSV
        header = ["Link", "GTIN13", "Price"]
        with open(f'{csv_name}.csv', 'a+', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            if file.tell() == 0:  # Write header only if the file is empty
                writer.writerow(header)
            writer.writerow([product_link, gtin, price])

        processed_count += 1

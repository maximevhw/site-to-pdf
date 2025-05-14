# pip install requests Pillow beautifulsoup4 playwright

import re
import os
import sys
import requests
from PIL import Image
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

max_depth = 2 # Max depth for crawling (how deep we go in following links)
visited_urls = {} # Dictionary to store URL and title pairs (URL as key, title as value)
visited_set = set() # Set to track visited URLs (avoid revisiting pages)


def crawl(url, depth):
    if depth < 0 or url in visited_set:
        return

    visited_set.add(url) # Mark URL as visited

    try:
        # Fetch the page
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get the title of the page (or a fallback if not found)
        title = soup.title.string.strip() if soup.title else 'No Title'

        # Store the URL and title in the dictionary
        visited_urls[url] = title

        # Find and follow all links on the current page
        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue

            full_url = urljoin(url, href)
            # Only follow internal links (same domain)
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                crawl(full_url, depth - 1)

    except Exception as e:
        print(f"Error at {url}: {e}")

def sanitize_filename(filename):
    # Replace all invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9.-]', '_', filename)  # Only allow a-z, A-Z, 0-9, period, and dash
    # Replace consecutive underscores with a single underscore
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized

def capture_full_page_screenshot(urls):
    with sync_playwright() as p:
        # Launch headless browser (no UI, background operation)
        browser = p.chromium.launch(headless=True)  # You can also use p.firefox or p.webkit
        
        # Go to the URL and take a full-page screenshot
        for index,(url, title) in enumerate(visited_urls.items(), 1):
            page = browser.new_page()
            page.goto(url)
            filename = f'{index}_{sanitize_filename(title)}'
            screenshot_path=f'screenshots/{filename}.png'
            page.screenshot(path=screenshot_path, full_page=True)
            print(f'Screenshot saved as {screenshot_path}')
        
        browser.close()

def merge_to_pdf():
    folder_path = 'screenshots/'
    output_pdf_path = f'{sanitize_filename(base_url)}.pdf'
    png_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
    images = []
    for png_file in png_files:
        image_path = os.path.join(folder_path, png_file)
        img = Image.open(image_path)
        img = img.convert('RGB')  # Convert image to RGB (required for PDF)
        images.append(img)
    # Save all images as a single PDF
    if images:
        images[0].save(output_pdf_path, save_all=True, append_images=images[1:], resolution=100.0, quality=95, optimize=True)
        print(f"PDF saved as {output_pdf_path}")
    else:
        print("No PNG files found in the folder.")


def main(base_url):
    print('Crawling....')
    crawl(base_url, depth=max_depth) # Start crawling from the base URL
    print(f"\nTotal pages crawled: {len(visited_urls)}")
    for url,title in visited_urls.items():
        print(f'{url},{title}')
    print('Creating screenshots...')
    capture_full_page_screenshot(visited_urls)
    print('Finished screenshots.')
    print('Creating pdf')
    merge_to_pdf()
    print('Finished pdf')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a domain.")
        sys.exit(1)
    base_url = sys.argv[1]
    main(base_url)

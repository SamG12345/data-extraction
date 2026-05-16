from playwright_stealth import Stealth
from playwright.sync_api import sync_playwright
import json
from lxml import html

class Scraper:
    def __init__(self):
        with Stealth().use_sync(sync_playwright()) as stealth:
            # open browser with stealth
            self.browser = stealth.chromium.launch(headless=True)
            self.tab = self.browser.new_page() # open a tab

            self.assign_url()
            self.close()

    def assign_url(self):
        url = ["https://ekantipur.com/entertainment", "https://ekantipur.com/cartoon"]

        # scarpping entertainment data
        ent_data = self.scrap_ent(url[0])

        # scrapping cartoon
        cart_data = self.scrap_cartoon(url[1])

        s = {"entertainment_news": ent_data, "cartoon of the day": cart_data}
        self.Write_json(s)


    def scrap_ent(self, url):
        """Navigates to the entertainment landing self.tab and scraps structured content data."""
        print(f"Navigating to Entertainment Category: {url}")
        self.tab.goto(url)
        
        # Simulate gentle user interaction to invoke image lazy loaders
        self.tab.evaluate("window.scrollBy(0, 1000)")
        self.tab.wait_for_timeout(1500)     # waiting

        print("Extracting card nodes dynamically...")
        scraped_data = self.tab.locator(".category-inner-wrapper").evaluate_all(
            """elements => elements.map(el => {
                const authorEl = el.querySelector('div.author-name a');
                const h2El = el.querySelector('h2');
                const imgEl = el.querySelector('img');
                const anchorEl = el.querySelector('a');
                
                return {
                    author: authorEl ? authorEl.innerText.trim() : "Unknown",
                    title: h2El ? h2El.innerText.trim() : "No Title",
                    img_src: imgEl ? imgEl.src : null,
                    href: anchorEl ? anchorEl.href : null
                };
            })"""
        )
        
        return scraped_data[:5]
    
    def scrap_cartoon(self, url):
        """Navigates to the cartoon landing self.tab and scraps structured content data."""
        print(f"Navigating to Cartoon Category: {url}")
        self.tab.goto(url)
        self.tab.wait_for_timeout(1000)
        
        data = self.scrap_cart_alt()
        return data


    def scrap_cart_alt(self):
        data = []
        for i in range(3):
            element = self.tab.locator(".cartoon-main-wrapper .cartoon-wrapper").nth(i)
            html_parsed = html.fromstring(element.inner_html())

            img_element = html_parsed.cssselect("img")
            desc_element = html_parsed.cssselect('.cartoon-description p')
            if img_element and desc_element:
                data.append({"image_url": img_element[0].get('src'), "author": desc_element[0].text_content().strip()})
        return data
    
    def Write_json(self, data):
        print("[+] Writing to JSON file.....")
        try:
            with open("output.json", 'w', encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.close()
        except Exception as e:
            print("[-] Error: ", e)
            return

    def close(self):
        self.browser.close()


def main():
    a = Scraper()

if __name__ == "__main__":
    main()
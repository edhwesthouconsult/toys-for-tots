import asyncio
import re
from bs4 import BeautifulSoup
from pyppeteer import launch
from tabulate import tabulate
urls = [
    "https://www.amazon.com/hz/wishlist/ls/143YHNGKKD0M0", #South East
    "https://www.amazon.com/hz/wishlist/ls/12XNX7IX4F90T", #North Central
    "https://www.amazon.com/hz/wishlist/ls/15I8V2W62KAM5", #North East
    "https://www.amazon.com/hz/wishlist/ls/1O9KCEX2M66V5", #South Central
    "https://www.amazon.com/hz/wishlist/ls/189ERQGRHTIED", #North West
    "https://www.amazon.com/hz/wishlist/ls/TIH9LADIA5FK" #South West
    "https://a.co/h27Hqol"
]

async def get(amazon_url: str, scroll_times: int) -> str:
    browser = await launch({"headless": True})
    tab = await browser.newPage()

    await tab.goto(amazon_url)

    for _ in range(scroll_times):
        await tab.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)

    return await tab.content()


def parse(content: str) -> list:
    soup = BeautifulSoup(content, "html.parser")
    name = soup.find("span", id="profile-list-name").text
    rows = []

    for i, span in enumerate(soup.find_all("li", {"data-itemid": re.compile(r"^[0-9A-Z]+$")})):
        item_name = span.find("a", id=re.compile("itemName_.*"))['title']
        requested = int(span.find("span", id=re.compile("itemRequested_.*")).text.strip())
        purchased = int(span.find("span", id=re.compile("itemPurchased_.*")).text.strip())

        rows.append([name,
                     i + 1,
                     span["data-itemid"],
                     item_name,
                     span["data-price"] if "." in span["data-price"] else "n/a",
                     requested,
                     purchased,
                     "YES" if requested == purchased else "NO"])
    return rows


results = []

for url in urls:
    results = results + parse(asyncio.get_event_loop().run_until_complete(get(amazon_url=url, scroll_times=50)))

print(tabulate(results, headers=["list", "#", "item", "item_name", "price", "requested", "purchased", "fulfilled"], tablefmt="pretty"))


content=tabulate(results, headers=["list", "#", "item", "item_name", "price", "requested", "purchased", "fulfilled"], tablefmt="pretty")
text_file=open("allresults121222.csv","w")
text_file.write(content)
text_file.close()
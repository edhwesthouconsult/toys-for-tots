import asyncio
import re
from bs4 import BeautifulSoup
from pyppeteer import launch
from tabulate import tabulate
urls = [
    "https://a.co/8aPxviZ", #SW
    "https://a.co/cJ5GTqX", #NW
    "https://a.co/4TDgx49", #NC
    "https://a.co/41Hiorg", #SC
    "https://a.co/74friED", #NE
    "https://a.co/2qLQt8Q", #SE
    "https://a.co/2HMl56m", #TR
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
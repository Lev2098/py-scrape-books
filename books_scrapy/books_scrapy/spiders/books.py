import scrapy
from scrapy.http import Response


def text_to_number(rating: str = "") -> int:
    rating = rating.lower()

    rating_map = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5
    }

    rating_text = next(
        (rate_text
         for rate_text in rating.split()
         if rate_text in rating_map),
        None
    )
    return rating_map.get(rating_text, 0)


def find_category(category: list[str] | None) -> str:
    if not category or len(category) < 3:
        return "Unknown"
    return category[2]


def take_description(response: Response) -> str:
    description_block = response.css("div#product_description")
    description = description_block.xpath(
        "following-sibling::p/text()"
    ).get()

    if description:
        return description.strip().replace("...more", "")
    return "No description available"


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = [
        "https://books.toscrape.com/catalogue/category/books_1/page-1.html"
    ]

    def parse_book_page(self, book: Response) -> dict:
        yield {
            "title": book.css(".product_main h1::text").get(),
            "price": book.css(
                ".product_main p.price_color::text"
            ).get().strip("£"),
            "amount_in_stock": book.xpath(
                "//th[text()='Availability']/following-sibling::td/text()"
            ).get(default="").strip(),
            "rating(1-5)": text_to_number(
                book.css("p.star-rating::attr(class)").get(default="")),
            "category": find_category(
                book.css("ul.breadcrumb li a::text").getall()),
            "description": take_description(book),
            "upc": book.xpath(
                "//th[text()='UPC']/following-sibling::td/text()"
            ).get(default="").strip(),
        }

    def parse(self, response: Response, **kwargs) -> None:
        for book in response.css("ol.row li"):
            book_link = response.urljoin(book.css("h3 a::attr(href)").get())
            yield scrapy.Request(book_link, callback=self.parse_book_page)
        next_page = response.css("ul.pager li.next a::attr(href)").get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

import scrapy
from datetime import datetime

class StartechSpider(scrapy.Spider):
    name = "startech"
    allowed_domains = ["startech.com.bd"]
    start_urls = ["https://www.startech.com.bd/"]
    mother_category_links = set()
    product_links = set()

    def parse(self, response):
        # Extract mother category links from the navigation
        mother_category_links = response.css('ul.navbar-nav > li.nav-item.has-child > a.nav-link::attr(href)').getall()
        self.mother_category_links.update(mother_category_links)
        self.logger.info(f"Found {len(mother_category_links)} mother category links")

        # Start with the first mother category link
        if self.mother_category_links:
            first_link = next(iter(self.mother_category_links))
            self.mother_category_links.discard(first_link)
            yield response.follow(first_link, callback=self.parse_category)

    def parse_category(self, response):
        # Extract product URLs from the current category page
        product_links_on_page = response.css('div.p-item a::attr(href)').getall()
        self.product_links.update(product_links_on_page)
        self.logger.info(f"Found {len(product_links_on_page)} product links on page: {response.url}")

        # Follow the pagination link for the "NEXT" page, if available
        next_page_url = response.xpath('//li/a[contains(text(), "NEXT")]/@href').get()
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            self.logger.info(f"Following pagination link: {next_page_url}")
            yield response.follow(next_page_url, callback=self.parse_category)
        else:
            self.logger.info(f"No more pages in category: {response.url}")

            # After collecting all products in this category, proceed to the next category
            if self.mother_category_links:
                next_category_link = next(iter(self.mother_category_links))
                self.mother_category_links.discard(next_category_link)
                yield response.follow(next_category_link, callback=self.parse_category)
            else:
                self.logger.info(f"Starting product data extraction for {len(self.product_links)} products")
                for idx, link in enumerate(self.product_links, start=1):
                    yield response.follow(link, callback=self.parse_product, meta={'product_index': idx})

    def parse_product(self, response):
        try:
            # Extract product data
            name = response.css('h1.product-name[itemprop="name"]::text').get()
            regular_price = response.css('del::text').get()
            discounted_price = response.css('ins::text').get()

            if discounted_price:
                discounted_price = discounted_price.strip()
                regular_price = regular_price.strip() if regular_price else None
            else:
                regular_price = response.css('td.product-info-data.product-price::text').get()
                if regular_price:
                    regular_price = regular_price.strip()

            stock_status = response.css('td.product-info-data.product-status::text').get()
            product_code = response.css('td.product-info-data.product-code::text').get()

            # Log the product details with timestamp and product index
            timestamp = datetime.now().isoformat()
            self.logger.info(f"Product details extracted from {response.url} at {timestamp}")
            self.logger.info(f" - Product Index: {response.meta['product_index']}")
            self.logger.info(f" - Name: {name}")
            self.logger.info(f" - Regular Price: {regular_price}")
            self.logger.info(f" - Discounted Price: {discounted_price}")
            self.logger.info(f" - Stock Status: {stock_status}")
            self.logger.info(f" - Product Code: {product_code}")

            # Yield the extracted data
            yield {
                'product_index': response.meta['product_index'],
                'name': name.strip() if name else None,
                'regular_price': regular_price,
                'discounted_price': discounted_price,
                'stock_status': stock_status.strip() if stock_status else None,
                'product_code': product_code.strip() if product_code else None,
                'url': response.url,
                'timestamp': timestamp
            }
        except Exception as e:
            self.logger.error(f"Error parsing product at {response.url}: {e}")

import scrapy

class StartechSpider(scrapy.Spider):
    name = "startech"
    allowed_domains = ["startech.com.bd"]
    start_urls = ["https://www.startech.com.bd"]

    def parse(self, response):
        # Follow the first navigation link
        first_nav_link = response.css('a.nav-link::attr(href)').get()
        if first_nav_link:
            yield response.follow(first_nav_link, self.parse_category)

    def parse_category(self, response):
        # Extract product URLs and follow them
        product_links = response.css('div.p-item a::attr(href)').getall()
        for link in product_links:
            yield response.follow(link, self.parse_product)
        
        # Follow pagination links if any
        next_page = response.css('ul.pagination a.page-link::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse_category)

    def parse_product(self, response):
        # Extract product name
        name = response.css('h4.p-item-name a::text').get()
        
        # Extract product price
        price = response.css('div.p-item-price span::text').get()
        if price:
            price = price.strip()
        
        # Determine stock status
        stock = self.determine_stock(response)

        yield {
            'name': name.strip() if name else None,
            'price': price if price else None,
            'stock': stock,
        }

    def determine_stock(self, response):
        # Check for elements indicating stock availability
        if response.css('span.st-btn.btn-add-cart'):
            return 'In Stock'
        else:
            return 'Out of Stock'

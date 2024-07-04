import scrapy


class StartechSpider(scrapy.Spider):
    name = "startech"
    allowed_domains = ["startech.com.bd"]
    start_urls = ["https://startech.com.bd"]

    def parse(self, response):
        pass

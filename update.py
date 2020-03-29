import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from courseSpider.spiders import course_spider


process = CrawlerProcess(get_project_settings())
process.crawl("courses")
process.start()





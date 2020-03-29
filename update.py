import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from courseSpider.spiders import course_spider
from graph_generator.concat import concat


process = CrawlerProcess(get_project_settings())
process.crawl("courses")
# the script will block here until the crawling is finished
process.start()
# After all courses are updated, produce the all_courses.jl file
concat("all_courses.jl")




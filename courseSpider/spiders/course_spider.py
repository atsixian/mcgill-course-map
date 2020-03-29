import scrapy
import os
from . import subject_data
from ..items import CoursespiderItem, CourseItemLoader
from scrapy.linkextractors import LinkExtractor

allurls = subject_data.start(
    f'https://mcgill.ca/study/2020-2021/courses/search').links

class CourseSpider(scrapy.Spider):
    name = 'courses'
    # pipeline setting
    custom_settings={
        'ITEM_PIPELINES' : {
            'courseSpider.pipelines.CoursespiderPipeline': 300,
        }
    }

    def start_requests(self):
        for url in allurls:
            yield scrapy.Request(url=url, meta={'start_url' : url}, callback=self.parse)

    def parse(self, response):
        ''' Get all course links with a certain css'''
        all_links = LinkExtractor(restrict_css=('.field-content a')).extract_links(response)
        
        # deal with each course individually
        for link in all_links: 
            yield response.follow(link.url, meta={'start_url' : response.meta['start_url']}, callback=self.parse_course)

        # parsing the next page
        next_page = response.css('li.pager-next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, meta={'start_url': response.meta['start_url']}, callback=self.parse)

    def parse_course(self, response):

        '''
            At first, I used the dictionary to assign value to each field, for example:

                course = CoursespiderItem()
                name = response.css('#page-title::text').get()
                course['name'] = name

            ItemLoader is exactly designed to populate fields, so it makes the whole process a lot cleaner.
            All the dirty work is in CourseItemLoader class.
        '''

        l = CourseItemLoader(item=CoursespiderItem(), response=response)
        l.add_css('name', '#page-title::text')
        l.add_xpath('prereq', "//li[contains(p, 'Prerequisite')]//a/@href")
        l.add_css('term', '.catalog-terms::text')
        l.add_value('link', response.url)
        l.add_value('subject', response.meta['start_url'])
        return l.load_item()

# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import os
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Identity, TakeFirst, MapCompose

# Loader to deal with data extracted from the website
class CourseItemLoader(ItemLoader):
    '''
        First I tried to use default_input_processor = TakeFirst(), but I realized that it was an array 
        again when went into the output_processor.
        I found an answer from https://stackoverflow.com/questions/46619150/scrapy-item-loader-default-processors :
            "It is written in this way:
            if processed_value: self._values[field_name] += arg_to_iter(processed_value). 
            After applying input process it is converted back to array so you can apply output processors. 
            As processors will assume input as an array only."

    '''
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    name_in = MapCompose(str.strip)

    prereq_in = MapCompose(lambda x: None if x is None else os.path.split(x)[1])
    prereq_out = Identity()

    term_in = MapCompose(lambda x: x.split(':')[1], str.strip)

    subject_in = MapCompose(lambda x: x[-4:])

    
    

class CoursespiderItem(scrapy.Item):
    '''
        name = course title
        prereq = list of prereqs
        link = link to this course
        term = which terms is this course offered; 'Not Offered' if none
        start_url = which site it is extracted from, used to store different subjects into different files
    '''

    name = scrapy.Field()
    prereq = scrapy.Field()
    term = scrapy.Field()
    link = scrapy.Field()
    subject = scrapy.Field()

class SubjectItem(scrapy.Item):

    name = scrapy.Field()
    link = scrapy.Field()
    code = scrapy.Field()
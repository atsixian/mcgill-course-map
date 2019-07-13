# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os
from pathlib import Path
from scrapy.exporters import JsonLinesItemExporter

OUTPUT_PATH = Path(__file__).parent.parent.joinpath('course_data')

class CoursespiderPipeline(object):

    def open_spider(self, spider):
        self.subject_exporters = {}

    def close_spider(self, spider):
        # Loop over all exporters to stop them
        for exporter in self.subject_exporters.values():
            exporter.finish_exporting()
            exporter.file.close()

    def _exporter_for_item(self, item):
        # Get the subject of the current item
        subject = item['subject']
        # If this is a new subject, create a new file with subject.jl as its name                                                                                                                                                                                                                                           ject.jl as name to store all courses of the same subject
        if subject not in self.subject_exporters:
            f = open(Path(OUTPUT_PATH).joinpath(f'{subject}.jl'), mode='wb')
            exporter = JsonLinesItemExporter(f)
            exporter.start_exporting()
            self.subject_exporters[subject] = exporter # add a new entry in the exporter dictionary
        return self.subject_exporters[subject]
    

    def process_item(self, item, spider):
        # Get the right exporter according to the subject
        exporter = self._exporter_for_item(item)
        exporter.export_item(item)
        return item

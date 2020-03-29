import requests
import re
from collections import namedtuple
from bs4 import BeautifulSoup

Courses = namedtuple('Courses', ['names', 'links', 'codes'])

def start(url, save=False):

    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    result = soup.select("#facetapi-facet-search-apicourses-block-field-subject-code .facetapi-inactive")

    NAMES = [ re.sub(' \(([0-9])*\)', '', n.contents[0]) for n in result ]
    LINKS = ['https://mcgill.ca' + l['href'] for l in result ]
    CODES = [ n[:4] for n in NAMES  ]

    # If you want to store the data:
    if save:
        import csv
        for (lst, filename) in [([NAMES], 'names'), ([LINKS], 'links'), ([CODES], 'codes')]:
            with open(f'{filename}.csv', 'w') as resultFile:
                wr = csv.writer(resultFile)
                wr.writerows(lst)
    return Courses(NAMES, LINKS, CODES)

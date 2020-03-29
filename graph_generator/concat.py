import shutil, glob
from pathlib import Path

'''
A helper script to concatenate all courses to a single all_courses file
'''

CURRENT_DIR = Path(__file__).parent
DATA_DIR = (CURRENT_DIR.parent / 'course_data').resolve()

def concat(output_name):
    with open((CURRENT_DIR / output_name).resolve(), 'wb') as outfile:
        for filename in DATA_DIR.glob('*.jl'):
            if filename == output_name:
                continue
            with open(filename, 'rb') as readfile:
                shutil.copyfileobj(readfile, outfile)

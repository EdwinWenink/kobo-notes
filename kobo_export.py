import os
import sys
import re
from bs4 import BeautifulSoup

"""
Changelog:

    - Now insert text comments before the highlight
    - First check if "note = annotation.content" is None
    - Add try - except clauses for optional fields
    - Added "progress"
    - Various ad-hoc fixes with if and try blocks
"""


"""
Trying to figure out the page numbering system
I'm happy if I can extract chapters

Alles lijkt met dezelfde prefix te beginnen.

point(/1/4/207/1:88)

(/1/4/2/1/158/1/2:182)

(/1/4/2/1/172:1)

(Chapter 2)
(/1/4/2/1/407/1/3:157

Ch3?(/1/4/2/1/312:1)

<fragment start="Ethics_Techn-nd_Engineering_split_006.html#point(/1/4/2/1/71/1/1:222)" end="Ethics_Techn-nd_Engineering_split_006.html#point(/1/4/2/1/71/1/1:366)" progress="0.0545455">

See: http://www.mobileread.mobi/forums/showthread.php?t=205062&page=6

Path resolution: http://idpf.org/epub/linking/cfi/epub-cfi.html#sec-path-res

Path examples: http://idpf.org/epub/linking/cfi/epub-cfi.html#sec-path-examples

Looks like this: http://idpf.org/epub/linking/cfi/epub-cfi.html
"""

# TODO find a method to extract pagenumbers (coded in target?)
# TODO Remove spaces from filenames, replace with underscores

tabs = re.compile(r"\t+")

args = sys.argv[1:]

if not args:
    print('usage: kobo_export.py filename')
    sys.exit(1)

filename = args[0]
title=[]
author=[]
publisher=[]

# TODO refactor; e.g. in a loop or some decorator pattern 
# https://stackoverflow.com/questions/17322208/multiple-try-codes-in-one-block
try:
    with open(filename, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml-xml")
except FileNotFoundError:
    print("The annotation file was not found")

# Not optional, this will halt the script
title = soup.find('title').get_text()

try:
    author = soup.find('creator').get_text() 
except AttributeError:
    author = ""
    print("Author is not specified")

try:
    publisher = soup.find('publisher').get_text()
except AttributeError:
    publisher = ""
    print("Publisher is not specified")

# YAML metadata
metadata ="""---
title: {}
author: {}
publisher: {}
---

""".format(title, author, publisher)

export = []

annotations = soup.find_all('annotation')

for annotation in annotations:
    date = annotation.date.get_text()
    citation = annotation.target.find('text').get_text()
    # TODO make this more robust
    progress= annotation.target.find('fragment').get("progress")
    # Introduced because get_text() fails on Knut Harmsun
    note = annotation.content
    if note:
        try:
            note = '\n\n> > {}'.format(note.find('text').get_text())
        except:
            print("No text field found for annotation")
    else: 
        note = ''
    # ( citation, progress, date, note )
    export.append((re.sub(tabs, '\t', citation.strip()), progress[:5], date[:10], note))

# Sort on progress; for some reason this is not always the default
export = sorted(export, key= lambda x: x[1])

# Format output for printing
export = ['{}. "{}" --- *{}, {}*{}\n\n'.format(i,*x) for i, x in enumerate(export) ]

with open(filename + ".md", "w", encoding="utf-8") as output:
    output.write(metadata)
    output.writelines(export)

print("Transcription finished")

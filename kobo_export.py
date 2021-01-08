import argparse
from pathlib import Path
import sys
import os
import re
from bs4 import BeautifulSoup

# TODO find a method to extract pagenumbers (coded in target?)
# TODO Remove spaces from filenames, replace with underscores

tabs = re.compile(r"\t+")

# ----------------
# Extraction logic
# ----------------

def extract(file_path=None, dir_path='./', output_dir='./'):
    '''
    If no file path is provided defaults to scanning 
    the current directory for annotation files

    '''
    if file_path:
        parse(file_path, output_dir)
    else:
        for root, dirs, files in os.walk(dir_path):
            files = [ f for f in files if f.endswith('.annot') ]
            for f in files:
                parse(os.path.join(root, f), output_dir)

def parse(file_path, output_dir):

    title=[]
    author=[]
    publisher=[]

    # TODO refactor; e.g. in a loop or some decorator pattern 
    # https://stackoverflow.com/questions/17322208/multiple-try-codes-in-one-block
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "lxml-xml")
    except FileNotFoundError:
        print("ERROR: The annotation file was not found")

    # Not optional, this will halt the script
    title = soup.find('title').get_text()

    try:
        author = soup.find('creator').get_text() 
    except AttributeError:
        author = ""
        print("WARNING: Author is not specified")

    try:
        publisher = soup.find('publisher').get_text()
    except AttributeError:
        publisher = "Unspecified"
        print("WARNING: Publisher is not specified")

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
        text = annotation.target.find('text')
        if text:
            citation = text.get_text().replace('\n', ' ')
        else:
            print("WARNING: Blank citation")
            citation = '...'

        # TODO make this more robust
        progress = annotation.target.find('fragment').get("progress")
        # Following clause introduced because get_text() fails for some EPUBs
        content = annotation.content
        if content:
            try:
                note = '\n\n> > {}'.format(content.find('text').get_text())
            except:
                note = ''
                print("WARNING: No text field found for annotation")
        else: 
            note = ''
        # ( citation, progress, date, note )
        export.append((re.sub(tabs, '\t', citation.strip()), progress[:5], date[:10], note))

    # Sort on progress; for some reason this is not always the default
    export = sorted(export, key= lambda x: x[1])

    # Format output for printing
    export = ['{}. "{}" --- *{}, {}*{}\n\n'.format(i,*x) for i, x in enumerate(export) ]

    filename = Path(file_path).stem.replace(' ', '_')
    with open(f"{output_dir}{filename}.md", "w", encoding="utf-8") as output:
        output.write(metadata)
        output.writelines(export)

    print(f"Transcription of {filename} finished")


# ------------------------------
# Parsing Command line arguments
# ------------------------------

parser = argparse.ArgumentParser(description="Extract KOBO annotations as Markdown files")
group = parser.add_mutually_exclusive_group()
group.add_argument("-f", "--file", help="path to annotation file to process ")
group.add_argument("-d", "--directory", help="root directory of all annotations")
parser.add_argument("-o", "--output", help="location of output folder (default: current folder)")
args = parser.parse_args()

if args.output:
    output_dir = args.output
else:
    output_dir = './'

if args.file:
    extract(file_path=args.file, output_dir=output_dir)
elif args.directory:
    extract(dir_path=args.directory, output_dir=output_dir)
else:
    # Default behavior:
    # - Extract all annotations under current directory
    # - Output markdown files in the current directory
    extract(output_dir=output_dir)




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


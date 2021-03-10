#!/usr/bin/env python

import os
import json
from pathlib import Path

path_root_logstack = '/home/logstack/_site/content'
base_url_logstack = 'http://192.168.20.38/logstack/'
saved_json = []

for md_path in Path (path_root_logstack).rglob ('*.md'):
    md_path_from_content = md_path.as_posix ()[len (path_root_logstack):] 

    path_components = [comp.strip () for comp in os.path.normpath (md_path_from_content).split (os.sep) if comp.strip ()]

    if path_components[-1] == "_index.md":
        continue

    # we need three information: title, content, author. But the content only up to 300 characters.
    metadata = {}
    with open (md_path.as_posix ()) as f_:
        lines = f_.read ().splitlines ()
        for i in range (1, len (lines)):
            if lines[i].strip () == '---':
                break

            prop = lines[i].split (':')
            metadata[prop[0]] = ":".join (prop[1:]).strip ()

        metadata['content'] = " ".join (lines[i+1:])[:500].strip ()
        metadata['link'] = base_url_logstack + \
                '/'.join (path_components[:-1]) + \
                '/' + os.path.splitext (path_components[-1])[0].lower ().replace (' ', '-')

        saved_json.append (metadata)

with open ('index.json', 'w') as f_:
    print ("Saved {} data".format (len (saved_json)))
    json.dump (saved_json, f_)
        

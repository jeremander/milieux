"""Cleans out HTML to prevent artifacts from appearing in the search index."""

import json
from pathlib import Path
import re


HTML_PATTERN = re.compile(r'<[^>]+>')


def clean_html(text):
    """Strips out HTML from a string."""
    return HTML_PATTERN.sub('', text).replace('&nbsp;', ' ')


def on_post_build(config, **kwargs):
    """Fixes a defect in the search feature for the 'readthedocs' theme.
    Duplicate entries exist, where one has escaped HTML in the title.
    We deduplicate these and remove the HTML."""
    search_index_path = Path(config['site_dir']) / 'search' / 'search_index.json'
    if search_index_path.exists():
        with open(search_index_path) as f:
            search_data = json.load(f)
        docs = search_data.get('docs', [])
        new_docs = []
        for doc in docs:
            if HTML_PATTERN.match(doc['title']):
                if 'title' in doc:
                    doc['title'] = clean_html(doc['title'])
            else:
                continue
            new_docs.append(doc)
        search_data['docs'] = new_docs
        with open(search_index_path, 'w') as f:
            json.dump(search_data, f, ensure_ascii=False, separators=(',', ':'))

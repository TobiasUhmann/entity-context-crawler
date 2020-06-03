### Link Extractor

Creates a directed link graph from the original Wikipedia dump. Every 
Wikipedia page is represented as a node that has directed edges to
all linked pages. The graph is represented as a simple SQLite database
with a single table that stores a `(from_doc, to_doc)` tuple for each
link where `from_doc` and `to_doc` are the hashed titles of the pages.
The titles are hashed to keep the database including its indexes below
32GB.

#### Input

By default, the link extractor expects the 
`enwiki-latest-pages-articles.xml` Wikipedia XML dump in the
current directory.

#### Output

The link extractor creates the `links.db` SQLite database with the
following structure:

```sql
CREATE TABLE links (
    from_doc int,      -- lowercase Wikipedia doc title
    to_doc int         -- lowercase Wikipedia doc title
)
```

#### Execute

The following command executes the link extractor in the background
and shows the current progress:

```bash
$ PYTHONUNBUFFERED=1;PYTHONHASHSEED=0 python link-extractor.py > link-extractor.stdout &
$ tail -f link-extractor.stdout
```

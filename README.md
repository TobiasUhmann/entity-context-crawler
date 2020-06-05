# Overview

Currently, the sentence sampler consists of the following components:

- The `LinkExtractor` creates a link graph from a full Wikipedia dump
  and stores it in the links database.
- The `EntityMatcher` searches a pre-processed Wikipedia dump for
  Freenode entities. To minimize false positives (e.g. find the movie
  "2012" in many unrelated articles), entities are only searched in
  articles linked to their main article. The entitie's occurrences
  are stored in the matches database.
- The `EntityLinker` determines how closely entities are linked to each
  other by comparing their contexts. In particular, it splits the
  entity matches' contexts into training and test contexts, stores
  the training contexts in Elasticsearch and subsequently queries 
  Elasticsearch for the contexts that best match the outheld test 
  contexts.

![Architecture](doc/architecture.png)

# Setup

1. Make sure that you have at least 150GB of free disk space
2. Clone the repository: <br>
   ```bash
   ~$ git clone https://gitlab.cs.hs-rm.de/tuhma001/sentence-sampler.git
   ```
3. Optionally, set up a local Python environment. Run the following
   commands to set up a local Anaconda environment: <br>
   ```bash
   ~/sentence-sampler$ conda create -p ./envs python=3.7
   ~/sentence-sampler$ conda activate ./envs
   ```
4. Put `deepca` next to the `sentence-sampler` clone
   ```batch
   ~$ ls
   deepca/
   sentence-sampler/
   ```
5. Install the dependencies, including `deepca` from its editable
   source: <br>
   ```batch
   ~/sentence-sampler$ pip install -r requirements.txt
   ~/sentence-sampler$ pip install -e ../deepca
   ```
6. By default the data files are expected to be in a `data/`
   subdirectory:
   ```batch
   ~/sentence-sampler$ ls data/
   entity2wikidata.json
   enwiki-2018-09.full.xml
   enwiki-latest-pages-articles.xml
   ```
7. Set up Elasticsearch

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

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

1. Make sure that you have at least 150GB of free disk space.
2. Clone the repository and mark the scripts as executable: <br>
   ```bash
   ~$ git clone https://gitlab.cs.hs-rm.de/tuhma001/sentence-sampler.git
   ~$ chmod +x sentence-sampler/bin/*.sh
   ```
3. Put `deepca` next to the `sentence-sampler` clone.
   ```batch
   ~$ ls
   deepca/
   sentence-sampler/
   ```
4. Optionally, set up a local Python environment. Run the following
   commands to set up a local Anaconda environment: <br>
   ```bash
   ~/sentence-sampler$ conda create -p ./envs python=3.7
   ~/sentence-sampler$ conda activate ./envs
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
7. Set up Elasticsearch.

# Usage

1. Create the link graph.
   ```batch
   ~/sentence-sampler/bin$ ./link-extractor --page-limit 1000
   Applied config:
       Wikipedia XML        ../data/enwiki-latest-pages-articles.xml
       Links DB             ../data/links.db
       In memory            False
       Commit frequency     10000
       Page limit           1000

   20:08:21 | COMMIT
   20:08:21 | 0 <page>s | 0 redirects | 0 links | 0 missing text
   20:08:27 | 1,000 <page>s | 267 redirects | 177,191 links | 0 missing text
   20:08:27 | COMMIT
   20:08:27 | DONE
   ```
2. Match the Freenode entities.
   ```batch
   ~/sentence-sampler/bin$ ./entity-matcher --doc-limit 1000
   Applied config:
      Freenode JSON        ../data/entity2wikidata.json
      Wikipedia XML        ../data/enwiki-2018-09.full.xml
      Links DB             ../data/links.db
      Matches DB           ../data/matches.db
      In memory            False
      Commit frequency     1000
      Doc limit            1000

   Missing URLs: 23
   20:11:21 | COMMIT
   20:11:21 | 0 Docs | Anarchism | 682 neighbors | 194 matches
   20:11:21 | 1 Docs | Autism | 335 neighbors | 32 matches
   20:11:21 | 2 Docs | Albedo | 114 neighbors | 31 matches
   ...
   20:11:48 | 999 Docs | Action Against Hunger | 1 neighbors | 0 matches
   20:11:48 | COMMIT
   20:11:48 | 1,000 Docs | AW | 1 neighbors | 0 matches
   20:11:48 | DONE
   ```
3. Analyse how closely the entity matches' contexts are linked:
   ```batch
   ~/sentence-sampler/bin$ ./entity-linker --limit-entities 10
   Applied config:
       Matches DB           ../data/matches.db
       Limit entities       10
       Context size         1000
       Limit contexts       None

   QUERY  political philosophy  'is a  that advocates self-governed societies based on voluntary institutions. These are often descri'
   -------------------------------------------------------------------
    174.9  anarchism             'Federations.\n\nPlatformism is a tendency within the wider anarchist movement based on the organisatio'
    161.4  philosophy            'Archibald Ogden, who threatened to quit if his employer did not publish it. While completing the nov'
    137.1  democracy             '(under the Law and Justice Party) to the Philippines (under Rodrigo Duterte).\n\nIn a Freedom House re'
    126.3  socialism             "lacking international recognition, remained in continuous existence until 1990.\n\nThe Polish People's"
    116.2  communism             'party until Lee Myung-bak won the presidential election of 2007.\n\nThe meaning of "conservatism" in t'
    113.0  ethics                'the nature of the mind and the  of creating artificial beings endowed with human-like intelligence w'
    109.4  government            'of the "Bundesrat" represent the s of the sixteen federated states and are members of the state cabi'
    100.7  Europe                'argued that political fragmentation (the presence of a large number of an states) made it possible f'
     98.5  German                'become Weimar Classicism.\n\nWeimar Classicism ( “"Weimarer Klassik"” and “"Weimarer Klassizismus"”) i'
     97.8  Soviet Union          'in Somino to the north (located in the Braslaw county of the Wilno Voivodeship); Manczin River to th'
   
   ...
   
     0 /  30 political philosophy           #     2 anarchism                       2 philosophy                      2 democracy                       2 socialism                     
    28 / 310 philosophy                     #    28 philosophy                     22 Aristotle                      19 ethics                         17 Plato                         
    32 / 350 anarchism                      #    32 anarchism                      31 democracy                      31 socialism                      28 communism                     
     4 /  70 French Revolution              #     5 government                      5 German                          5 Europe                          5 Paris                         
     3 /  30 libertarianism                 #     3 anarchism                       3 libertarianism                  2 socialism                       2 democracy                     
     0 /  20 Jesus Christ                   #     2 Christianity                    2 Catholic Church                 2 Latin                           2 Greek                         
     0 /  20 English Civil War              #     2 England                         2 World War II                    2 Paris                           1 American Revolutionary War    
     0 /  10 Roundhead                      #     1 anarchism                       1 French Revolution               1 English Civil War               1 philosophy                    
     0 /  10 Jean-Jacques Rousseau          #     1 anarchism                       1 French Revolution               1 English Civil War               1 philosophy                    
     1 /  20 Karl Marx                      #     2 economics                       2 Europe                          2 German                          1 Karl Marx                     
   ```

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

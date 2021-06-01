Many NLP-related tasks, such as relation extraction or knowledge graph completion, involve the processing of entities. Some of them require textual information about the entities. One way to automatically obtain large amounts of text information for many entities is crawling the web.

The `Entity Context Crawler (ECC)` is such a crawler for the Wikipedia. It takes a Wikipedia dump and a list of entities and generates a database with entity contexts it finds all over the Wikipedia. Note, that the resulting contexts do not necessarly describe the specific entity, but only mention it, possibly as part of a long sentence.

In more detail, `ECC` requires the URLs of the enities' Wikipedia articles, which it uses to find linked articles. `ECC` then collects all sentences that mention the entity from the entity's article itself as well as from the linked articles. The search is limited to directly linked neighbor articles to reduce the noise of false positives.

# Input/Output Data

`ECC` requires a Wikipedia XML dump and a JSON containing the entities. The `Wikipedia XML` can be downloaded from https://dumps.wikimedia.org/. The `Entities JSON` must have the following format, whereby the entity IDs could be Freebase or Wikidata IDs, for example:

```json
{
  "ID_1": {
    "label": "Denton",
    "wikipedia": "https://en.wikipedia.org/wiki/Denton,_Texas"
  },
  "ID_2": {
    "label": "El Paso",
    "wikipedia": "https://en.wikipedia.org/wiki/El_Paso,_Texas"
  }
}
```

The generated `Contexts DB` is an SQLite database with the schema below. It is not normalized to simplify debugging.

```sqlite
CREATE TABLE contexts (
    id              INT,
    
    entity          INT,
    entity_label    TEXT,
    mention         TEXT,
    page_title      TEXT,
    context         TEXT,
    masked_context  TEXT,
    
    PRIMARY KEY (id)
)
```

# Setup

Optionally, create a dedicated Python environment, e.g. a local Anaconda environment:

```bash
$ conda create --prefix conda39 python=3.9
$ conda activate conda39/
```

Install `ECC`, e.g. via `pip`:

```bash
$ pip install entity-context-crawler 
```

Download the large SpaCy language model used for sentence recognition:

```bash
$ spacy download en_core_web_lg
```

ECC can then be used via the `ecc` command:

```bash
$ ecc --help
```

# Usage

The context crawling happens in two steps: First, the `Matches DB` is created that contains all positions (article / character offset) where the entity is mentioned. Second, `ECC` selects a fixed number of random matches per entity and stores their surrounding sentences in the `Contexts DB`.

To create the `Matches DB`, run `ecc build-matches-db`:

```bash
$ ecc build-matches-db wikipedia.xml entities.json matches.db
```

For the English Wikipedia, the script might run for well over 24h. You might want to run it in the background and prevent the hangup signal when running `ECC` over SSH:

```bash
$ nohup ecc build-matches-db wikipedia.xml entities.json matches.db > build_matches_db.stdout &
$ tail -f build_matches_db.stdout
```

To build the `Contexts DB` from the created `Matches DB` with 100 contexts per entity by default, execute `ecc build-contexts-db`:

```bash
$ ecc build-contexts-db entities.json matches.db contexts.db
```

Just like building the `Matches DB`, this might take a while and could be run in the background as follows:

```bash
$ nohup ecc build-contexts-db entities.json matches.db contexts.db > build_contexts_db.stdout &
$ tail -f build_contexts_db.stdout
```

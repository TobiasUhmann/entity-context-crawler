# Introduction

Knowledge graphs represent entities and their relationship to each other as a graph. The graph's nodes represent entities like *"Angela Merkel"* and *"Germany"*. The graph's directed edges represent relations between entities like *"is chancellor of"* which holds true for *"Angela Merkel"* and *"Germany"* as of 2020.

There are well maintained knowledge graphs for general knowledge as described in Wikipedia, for example. For specific domains, however, there are rarely comprehensive knowledge graphs because of the high effort to create them. However, the domain-specific entities are often known and there are large amounts of unstructured data such as texts describing the entities and their relationships.

This is referred to as an *open world scenario*: A knowledge graph exists for the known *closed world entities* and the relations between them. In addition, there are the known *open world entities*, whose relations are unknown. However, these relations can be derived from the existing, unstructured data that describes the open world entities.


# Project Scope

This project provides tools for setting up a baseline model that follows a primitive approach to predict an open world entity's triples: It looks up the closed world entity most similar to the open world entity using Elasticsearch, which uses TF-IDF as a measure of similarity, and assumes that the closed world entity's triples also apply to the open world entity. For example, if *"Emmanuel Macron"* is an open world entity whose most similar closed world entity is *"Angela Merkel"* for who the relation *"has profession"* towards the entity *"politician"* is true, the model assumes that this also applies to *"Emmanuel Macron"*.

Furthermore, the project contains an evaluation framework for comparing other models to the baseline, tools for running a grid search to find the best hyperparameters to train these models, as well as a browser UI that allows browsing the data.


# Setup

1. Make sure that you have at least 150GB of free disk space.

1. Clone the `sentence-sampler` repository and mark the scripts as executable:
   ```
   ~$ git clone https://gitlab.cs.hs-rm.de/tuhma001/sentence-sampler.git
   ~$ chmod +x sentence-sampler/bash/*.sh
   ```

1. Clone the `deepca` and the `ryn` repositories next to the `sentence-sampler` directory:
   ```
   ~$ git clone https://git.ramlimit.de/deepca/deepca.git
   ~$ git clone https://git.ramlimit.de/deepkg/ryn.git
   ~$ ls
   deepca/
   ryn/
   sentence-sampler/
   ```

1. Optionally, set up a local Python environment. Run the following
   commands to set up a local Anaconda environment:
   ```
   ~/sentence-sampler$ conda create -p conda/ python=3.8
   ~/sentence-sampler$ conda activate conda/
   ```

1. Install the dependencies, including `deepca` from its editable
   source:
   ```
   ~/sentence-sampler$ pip install -e ../deepca/
   ~/sentence-sampler$ pip install -r ../deepca/requirements/all.txt
   ~/sentence-sampler$ pip install -e ../ryn/
   ~/sentence-sampler$ pip install -r ../ryn/requirements.txt
   ~/sentence-sampler$ pip install -r requirements.txt
   ```

1. Download the spaCy model:
   ```
   ~$ python -m spacy download en_core_web_lg
   ```

1. Provide the required data files in the `data/` directory as described below in section [Data Files](#data-files).

1. Set up Elasticsearch.


# Commands Overview

The following diagram gives an overview how the available commands (yellow) are related and what documents (green) and databases are produced and consumed:

![Commands Overview](doc/commands_overview.png)

The upper part of the pipeline samples the entities' contexts in two steps:

- [`build-matches-db`](../../wikis/Commands/build-matches-db) takes the `Wiki XML dump` and the `Wikidata JSON `containing the mapping from the entities' QIDs to the respective Wikidata and produces the `Matches DB` that stores all matches of entities in the Wikipedia.
- [`build-contexts-db`](../../wikis/Commands/build-contexts-db) takes the matches from the `Matches DB` and samples a limited number of contexts for each entity. It also requires the `QID -> ryn ID TXT` mapping as it also stores the entities' ryn IDs. The result is the `Contexts DB`.

The expressiveness of the contexts in the `Contexts DB` can be tested by building and subsequently quering the "Elasticsearch test":

- [`build-es-test`](../../wikis/Commands/build-es-test) stores 30% of the contexts from the `Contexts DB` in a database and the other 70% in an Elasticsearch index.
- [`query-es-test`](../../wikis/Commands/query-es-test) is called with an entity that must be present in the `30% contexts DB` and queries the `70% Contexts ES Index` for the entity's contexts. The resulting entity should be similar to the query entity.
- [`eval-es-test`](../../wikis/Commands/eval-es-test) queries the `70% Contexts ES Index` for all the entities from the `30% Contexts DB` and yields metrics that indicate the overall expressiveness of the contexts.

The lower part of the actual pipeline builds the baseline model from the `Contexts DB` which can then be queried:

- [`build-baseline`](../../wikis/Commands/build-baseline) splits the contexts from the `Contexts DB` into open and closed world entities using the information fromt the `OpenKE dataset`. As a result, the `OW Contexts DB` contains the contexts of the open world entities while the `CW Contexts ES Index` contains the contexts of the closed world entities.
- [`eval-model`](../../wikis/Commands/eval-model) can be used to evaluate link prediction models, including the baseline model. `eval-model` generally requires the `OpenKE dataset` to differentiate between open and closed world entities. In order to be able to run the baseline model it furthermore requires the `OW Contexts DB` and the `CW Contexts ES Index` built by `build-baseline`.


# Data Files

The example used in this documentation assume the following structure of the data directory:

```
data/
    oke.fb15k237_30061990_50/                   # OpenKE dataset directory
    contexts-v7-enwiki-20200920-100-500.db      # Contexts DB
    enwiki-20200920.xml                         # Wiki XML dump
    matches-v6-enwiki-20200920.db               # Matches DB
    wikidata-v1-2020-12-31.json                 # Wikidata JSON
```

Further details can be found in the wiki:
- [OpenKE Dataset Directory](../../wikis/Data-Files/OpenKE-Dataset-Directory)
- [Contexts DB](../../wikis/Data-Files/Contexts-DB)
- [Wikidata JSON](../../wikis/Data-Files/Wikidata-JSON)
- [Wiki XML Dump](../../wikis/Data-Files/Wiki-XML-Dump)
- [Matches DB](../../wikis/Data-Files/Matches-DB)

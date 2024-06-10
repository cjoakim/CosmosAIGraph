# CosmosAIGraph : Code Generation

A relatively new addition to this codebase is code generation,
which currently can be used to:

- Generate an OWL ontology file
- Fully generate a standalone class RdflibTriplesBuilder, called by GraphBuilder

Both of the above generators use **metadata** that can be mined
from your source input data for your graph.  The format of this
data will obviously vary by customer.  But the input data will 
contain necessary information that can be **wrangled** to form
the metadata.

### Example Metadata

This repository contains two example files, for the simple **IMDb**
movies graph.  One file identifies the metadata for the **verticies** 
(or entities) in your graph, while the other file identifes the **edges**
(or relationships).

```
impl1/app_console/meta/edge_signatures_imdb.json
impl1/app_console/meta/vertex_signatures_imdb.json
```

### Data Wrangling

A simple python program can be created to read your input files,
observe its structure, and produce two metadata files similarly
structured to the above files.

### Execute the Generators

Once your metadata files exist, you can generate code as follows:

```
> cd .\app_console\

> .\venv\Scripts\Activate.ps1

> python main.py generate_owl meta/vertex_signatures_imdb.json meta/edge_signatures_imdb.json http://cosmosdb.com/imdb

...
file written: tmp/generated.owl

> python main.py generate_rdflib_triples_builder meta/vertex_signatures_imdb.json

...
file written: tmp/rdflib_triples_builder.py
```

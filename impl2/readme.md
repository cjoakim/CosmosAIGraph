# CosmosAIGraph - imdb graph 

This page documents how to create and use a large-sized graph for CosmosAIGraph
by using the public IMDb dataset.

This process is described in these four sections of this page:
- **1. Data Wrangling**
- **2. Data Loading to Cosmos DB**
- **3. Load the RDF Graph from Cosmos DB vCore**
- **4. Querying the RDF Graph**
- **5. Run the Web Application**

This IMDb dataset is also one of the graphs in the
[AltGraph](https://github.com/cjoakim/azure-cosmosdb-altgraph) reference application.

---

## 1. Data Wrangling

### Download the raw TSV data

Download each of these URLs to the to the Downloads directory of your computer.
Extract each gz file, and copy the resulting *.tsv files to the data\ directory
beneath this imdb\ directory.  Create the data\ directory if it doesn't already exist.

```
https://datasets.imdbws.com/name.basics.tsv.gz
https://datasets.imdbws.com/title.basics.tsv.gz
https://datasets.imdbws.com/title.principals.tsv.gz
https://datasets.imdbws.com/title.ratings.tsv.gz
```

List of the resulting files in the data\ directory:

```
PS ...\data> dir

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----         4/26/2024   3:58 PM      826725520 name.basics.tsv
-a----         4/26/2024   3:59 PM      922302209 title.basics.tsv
-a----         4/26/2024   3:59 PM     3797230375 title.principals.tsv
-a----         4/26/2024   3:59 PM       24830726 title.ratings.tsv
```

See the file descriptions here:
https://developer.imdb.com/non-commercial-datasets/

**NOTE: Both the raw IMDB tsv files, and the resulting json and nt files, are intentionally git-ignored due to their size.**  Users of this repo are expected to download the TSV data and execute this wrangling process if necessary.

### Execute the data-wrangling process

#### First create the Python Virtual Environment

```
.\venv.ps1
 - or -
./venv.sh
```

After the virtual environment is created, you'll need to **activate** it
each time you navigate into this directory in your Terminal application.
See the above venv scripts for details.

#### Then execute the all-in-one wrangling script

```
mkdir tmp
mkdir rdf

.\wrangle.ps1
 - or -
./wrangle.sh
```

Parts of the wrangle shell script are shown below.  It shows the logical outline
of the wrangling process steps implemented in Python script **wrangle.py**.

Python script **wrangle.py** provides a good example of how to transform your raw CSV or TSV
files into Cosmos DB JSON documents and an rdflib graph.

```
echo "=== explore_imdb_tsv_files ..."
python wrangle.py explore_imdb_tsv_files > docs\tsv_file_info.txt

echo "=== step0_print_criteria ..."
python wrangle.py step0_print_criteria

echo "=== step1_filter_ratings ..."
python wrangle.py step1_filter_ratings

echo "=== step2_filter_titles ..."
python wrangle.py step2_filter_titles

echo "=== step3_gather_names ..."
python wrangle.py step3_gather_names

echo "=== step4_gather_principals ..."
python wrangle.py step4_gather_principals > tmp\step4_gather_principals.txt

echo "=== step5_print_selected_entities ..."
python wrangle.py step5_print_selected_entities

echo "=== step6_build_rdf_triples ..."
python wrangle.py step6_build_rdf_triples

echo "=== step10_load_rdflib_graph ..."
python wrangle.py step10_load_rdflib_graph
```

Steps 1-5 use the following criteria for including non-adult titles,
and related principals/roles:

```
Selection Criteria:
  MIN_RATING:  6.0
  MIN_YEAR:    1980
  MIN_MINUTES: 75
  ROLES:       ['actor', 'actress', 'director', 'producer']
```

Many rows in the very large IMDb dataset do not meet this filtering criteria
and thus are excluded from the graph produced by this process.

**Step 6** creates the **rdf/imdb.nt** **"triples"** file from the extracted data.
Each triple consists of three parts - subject, predicate, and object.
These three values include references to their ontology definition.
See the sample triples shown at the bottom of this page.

**Step 10** loads the imdb.nt file into an in-memory rdflib graph, serializes
the graph to another nt file, iterates the graph, and queries the graph
for the principals (i.e. - People) in the movie Footloose.  Output shown below:

```
parsing triples_file
graph loaded in 64.787656416 seconds
graph serialize in 64.787656416 seconds
graph iterated in 3.938760041 seconds, 5721065 triples
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0000102'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001742'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001475'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001848'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001606'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0000572'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0490855'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0329829'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0564589'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0950281'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0006889'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0705135'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0951722'),)
graph queried in 0.051442875 seconds, 13 triples
```

#### Graph Metadata

```
Number of Movies:       150,569
Number of Principals:   543,936
Number of Triples:    5,721,011
```

One triple for each Movie and Principal.
The remaining triples represent the attributes and relationships.

#### Graph Ontology

The custom **imdb.owl** file is shown below.  It leverages standard namespaces
(i.e. - xmlns:rdf, xmlns:xsd, etc.) and defines two custom classes - Movie and Person.
It also defines attributes for each of these classes, as well as the datatype
of the attribute.

```
<?xml version="1.0"?>

<rdf:RDF
  xmlns      = "http://cosmosdb.com/imdb#"
  xmlns:owl  = "http://www.w3.org/2002/07/owl#"
  xmlns:rdf  = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:rdfs = "http://www.w3.org/2000/01/rdf-schema#"
  xmlns:xsd  = "http://www.w3.org/2001/XMLSchema#">

  <owl:Ontology rdf:about="">
    <rdfs:comment>
      A custom ontology for the IMDb graph
    </rdfs:comment>
    <rdfs:label>IMDb Ontology</rdfs:label>
  </owl:Ontology>

  <!-- Classes defined below -->

  <owl:Class rdf:ID="Movie">
    <rdfs:label xml:lang="en">Movie</rdfs:label>
    <rdfs:comment xml:lang="en">A Movie in the IMDb dataset</rdfs:comment>
  </owl:Class>

  <owl:Class rdf:ID="Person">
    <rdfs:label xml:lang="en">Person</rdfs:label>
    <rdfs:comment xml:lang="en">A Person related to a Movie in the IMDb dataset</rdfs:comment>
  </owl:Class>

  <!-- Movie attributes below -->

  <owl:ObjectProperty rdf:ID="title">
	<rdfs:label xml:lang="en">title</rdfs:label>
	<rdfs:comment xml:lang="en">Title of a Movie</rdfs:comment>
    <rdfs:domain rdf:resource="#Movie" />
    <rdfs:range  rdf:resource="http://www.w3.org/2001/XMLSchema#string" />
  </owl:ObjectProperty>

  <owl:ObjectProperty rdf:ID="year">
	<rdfs:label xml:lang="en">year</rdfs:label>
	<rdfs:comment xml:lang="en">Year the Movie was produced</rdfs:comment>
    <rdfs:domain rdf:resource="#Movie" />
    <rdfs:range  rdf:resource="http://www.w3.org/2001/XMLSchema#int" />
  </owl:ObjectProperty>

  <owl:ObjectProperty rdf:ID="rating">
	<rdfs:label xml:lang="en">rating</rdfs:label>
	<rdfs:comment xml:lang="en">Rating of the Movie</rdfs:comment>
    <rdfs:domain rdf:resource="#Movie" />
    <rdfs:range  rdf:resource="http://www.w3.org/2001/XMLSchema#float" />
  </owl:ObjectProperty>

  <owl:ObjectProperty rdf:ID="genre">
	<rdfs:label xml:lang="en">genre</rdfs:label>
	<rdfs:comment xml:lang="en">Genre of the Movie</rdfs:comment>
    <rdfs:domain rdf:resource="#Movie" />
    <rdfs:range  rdf:resource="http://www.w3.org/2001/XMLSchema#string" />
  </owl:ObjectProperty>

  <owl:ObjectProperty rdf:ID="principal">
	<rdfs:label xml:lang="en">principal</rdfs:label>
	<rdfs:comment xml:lang="en">A Principal (actor, actress, director, producer) of the Movie</rdfs:comment>
    <rdfs:domain rdf:resource="#Movie" />
    <rdfs:range  rdf:resource="http://www.w3.org/2001/XMLSchema#string" />
  </owl:ObjectProperty>

  <!-- Person attributes below -->

  <owl:ObjectProperty rdf:ID="name">
	<rdfs:label xml:lang="en">name</rdfs:label>
	<rdfs:comment xml:lang="en">Name of a Person</rdfs:comment>
    <rdfs:domain rdf:resource="#Person" />
    <rdfs:range  rdf:resource="http://www.w3.org/2001/XMLSchema#string" />
  </owl:ObjectProperty>

  <owl:ObjectProperty rdf:ID="born">
	<rdfs:label xml:lang="en">born</rdfs:label>
	<rdfs:comment xml:lang="en">Year of Birth of a Person</rdfs:comment>
    <rdfs:domain rdf:resource="#Person" />
    <rdfs:range  rdf:resource="http://www.w3.org/2001/XMLSchema#int" />
  </owl:ObjectProperty>

  <owl:ObjectProperty rdf:ID="died">
	<rdfs:label xml:lang="en">died</rdfs:label>
	<rdfs:comment xml:lang="en">Year of Death of a Person</rdfs:comment>
    <rdfs:domain rdf:resource="#Person" />
    <rdfs:range  rdf:resource="http://www.w3.org/2001/XMLSchema#int" />
  </owl:ObjectProperty>

  <owl:ObjectProperty rdf:ID="in_movie">
	<rdfs:label xml:lang="en">in_movie</rdfs:label>
	<rdfs:comment xml:lang="en">Movie ID that a Person was a Principal in</rdfs:comment>
    <rdfs:domain rdf:resource="#Person" />
    <rdfs:range  rdf:resource="http://www.w3.org/2001/XMLSchema#string" />
  </owl:ObjectProperty>

</rdf:RDF>
```

#### Sample nt triples

Triples with tt0087277 (Footloose)

```
<http://cosmosdb.com/imdb/tt0087277> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://cosmosdb.com/imdb#Movie> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#title> "footloose" .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#year> "1984" .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#rating> "6.6" .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#genre> "drama" .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#genre> "music" .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#genre> "romance" .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0000102> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0001742> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0001475> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0001848> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0001606> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0000572> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0490855> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0329829> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0564589> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0950281> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0006889> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0705135> .
<http://cosmosdb.com/imdb/tt0087277> <http://cosmosdb.com/imdb#principal> <http://cosmosdb.com/imdb/nm0951722> .
```

Triples with nm0000102 (Kevin Bacon)

```
<http://cosmosdb.com/imdb/nm0000102> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://cosmosdb.com/imdb#Person> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#person_name> "Kevin Bacon" .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#person_born> "1958" .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#person_died> "-1" .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0080761> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0083833> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0087277> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0093403> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0093748> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0094318> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0096926> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0099582> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0100814> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0104257> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0110997> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0112384> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0112453> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0113870> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0116920> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0117665> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0118980> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0120303> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0120890> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0156812> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0164181> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0207607> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0280380> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0327056> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0361127> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0373450> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0485851> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0804461> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0822849> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt0870111> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt1019454> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt1185431> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt1270798> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt12747748> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt1355683> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt1512235> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt1699509> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt1781840> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt2290075> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt3813310> .
<http://cosmosdb.com/imdb/nm0000102> <http://cosmosdb.com/imdb#in_movie> <http://cosmosdb.com/imdb/tt5226220> .
```

---

## Next Steps

Steps 1-5 create the following JSON files in the tmp directory:
```
titles.json   <-- the filtered Movies (per above selection criteria)
names.json    <-- the Principals (actor, actress, director, producer) in the filtered Movies
```

The elements (i.e. - documents) in each of these two files can be loaded
into Cosmos DB and the rdflib in-memory graph can be loaded from these 
Cosmos DB documents.

### Example Documents

This document in **titles.json** represents the movie **Footloose**.

```
{
  "tconst": "tt0087277",
  "title": "footloose",
  "year": 1984,
  "rating": 6.6,
  "genres": [
    "drama",
    "music",
    "romance"
  ],
  "principals": {
    "nm0000102": "actor",
    "nm0001742": "actress",
    "nm0001475": "actor",
    "nm0001848": "actress",
    "nm0001606": "actor",
    "nm0000572": "actress",
    "nm0490855": "actor",
    "nm0329829": "actress",
    "nm0564589": "actress",
    "nm0950281": "actor",
    "nm0006889": "director",
    "nm0705135": "producer",
    "nm0951722": "producer"
  }
}
```

This document in **names.json** represents the actor **Kevin Bacon**.

```
{
  "nconst": "nm0000102",
  "name": "Kevin Bacon",
  "born": 1958,
  "died": -1,
  "titles": {
    "tt0080761": "actor",
    "tt0083833": "actor",
    "tt0087277": "actor",
    "tt0093403": "actor",
    "tt0093748": "actor",
    "tt0094318": "actor",
    "tt0096926": "actor",
    "tt0099582": "actor",
    "tt0100814": "actor",
    "tt0104257": "actor",
    "tt0110997": "actor",
    "tt0112384": "actor",
    "tt0112453": "actor",
    "tt0113870": "actor",
    "tt0116920": "director",
    "tt0117665": "actor",
    "tt0118980": "actor",
    "tt0120303": "actor",
    "tt0120890": "actor",
    "tt0156812": "actor",
    "tt0164181": "actor",
    "tt0207607": "actor",
    "tt0280380": "actor",
    "tt0327056": "actor",
    "tt0361127": "actor",
    "tt0373450": "actor",
    "tt0485851": "actor",
    "tt0804461": "actor",
    "tt0822849": "actor",
    "tt0870111": "actor",
    "tt1019454": "actor",
    "tt1185431": "actor",
    "tt1270798": "actor",
    "tt12747748": "actor",
    "tt1355683": "actor",
    "tt1512235": "actor",
    "tt1699509": "actor",
    "tt1781840": "actor",
    "tt2290075": "actor",
    "tt3813310": "actor",
    "tt5226220": "actor"
  }
}
```

---

## 2. Data Loading to Cosmos DB vCore

### Display your CAIG_ environment variables

```
python main.py display_caig_env_vars
```

### Create Cosmos DB vCore collections and indexes

```
python main.py create_vcore_collections_and_indexes

...

2024-04-28 04:14:18,575 - imdb indexes after:
{
  "_id_": {
    "v": 2,
    "key": [
      [
        "_id",
        1
      ]
    ]
  },
  "doctype_1": {
    "v": 2,
    "key": [
      [
        "doctype",
        1
      ]
    ]
  },
  "nconst_1": {
    "v": 2,
    "key": [
      [
        "nconst",
        1
      ]
    ]
  },
  "tconst_1": {
    "v": 2,
    "key": [
      [
        "tconst",
        1
      ]
    ]
  }
}
```

### Load the Cosmos DB vCore 'imdb' container with People and Movies

```
python main.py load_vcore

...

2024-04-28 04:15:56,199 - connected to vcore
2024-04-28 04:15:56,199 - using vcore db: caig, collection: imdb
2024-04-28 04:15:56,199 - pausing 10 seconds before deleting then loading the documents...
DeleteResult({'ok': 1, 'n': 694505}, acknowledged=True)

...

load_names_filtered, len: 543936
load_titles, len: 150569

...

executing batch 6944 with 100 operations, doctype movie
BulkWriteResult({'writeErrors': [], 'writeConcernErrors': [], 'nInserted': 100, 'nUpserted': 0, 'nMatched': 0, 'nModified': 0, 'nRemoved': 0, 'upserted': []}, acknowledged=True)
executing batch 6945 with 100 operations, doctype movie
BulkWriteResult({'writeErrors': [], 'writeConcernErrors': [], 'nInserted': 100, 'nUpserted': 0, 'nMatched': 0, 'nModified': 0, 'nRemoved': 0, 'upserted': []}, acknowledged=True)
executing batch 6946 with 69 operations, doctype movie
BulkWriteResult({'writeErrors': [], 'writeConcernErrors': [], 'nInserted': 69, 'nUpserted': 0, 'nMatched': 0, 'nModified': 0, 'nRemoved': 0, 'upserted': []}, acknowledged=True)
vcore loaded in 374.345505334 seconds, 694505 documents, 6946 batches
```

Note: this load was done from my home computer and network.  Results will be faster in Azure.

#### Verify the load in mongosh

```
[mongos] caig> db.imdb.countDocuments()
694505

[mongos] caig> db.imdb.findOne()
{
  _id: '8bd07d8f-25d0-4862-bb61-f229a7dc4a68',
  nconst: 'nm0000001',
  name: 'Fred Astaire',
  born: 1899,
  died: 1987,
  titles: { tt0082449: 'actor' },
  doctype: 'person'
}
```

---

## 3. Load the RDF Graph from Cosmos DB vCore


```
python main.py load_graph_from_vcore

...

adding person doc: 541000 {'_id': '8a8af30c-463d-4f7d-bc64-8d34bd8abece', 'nconst': 'nm0747149', 'name': 'Rahul Roy', 'born': 1966, 'died': -1, 'titles': {'tt0107060': 'actor', 'tt0149573': 'actor', 'tt0395557': 'actor', 'tt11112532': 'actor', 'tt12395840': 'actor', 'tt3239126': 'actor', 'tt8537578': 'actor', 'tt9337544': 'actor'}, 'doctype': 'person'}
adding person doc: 542000 {'_id': 'a41e595c-cd60-4c8d-af58-18275ece9fdf', 'nconst': 'nm0754244', 'name': 'Nicolás Saad', 'born': 1970, 'died': -1, 'titles': {'tt0177915': 'director'}, 'doctype': 'person'}
adding person doc: 543000 {'_id': '5def74a9-aedb-4318-9c79-1ff05a3c84c4', 'nconst': 'nm0760457', 'name': 'Dee Dee Samuels', 'born': -1, 'died': -1, 'titles': {'tt1686306': 'producer'}, 'doctype': 'person'}
load_graph_from_vcore - graph loaded in 66.103941958 seconds, 694505 documents
load_graph_from_vcore - graph iterated in 4.049040292 seconds, 5721065 triples
```

Note: this load was done from my home computer and network.  Results will be faster in Azure.

---

## 4. Querying the RDF Graph

Execute the same **load_graph_from_vcore** function as shown above,
but with the **--queries** command-line option.

Several SPARQL queries will be executed vs the in-memory rdflib
graph after the graph is loaded from vCore.

```
python main.py load_graph_from_vcore --queries

...

execute_sparql_query:
PREFIX c: <http://cosmosdb.com/imdb#>
SELECT ?o
WHERE {
    <http://cosmosdb.com/imdb/nm0000102> c:in_movie ?o .
}
LIMIT 100

(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0080761'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0083833'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0087277'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0093403'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0093748'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0094318'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0096926'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0099582'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0100814'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0104257'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0110997'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0112384'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0112453'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0113870'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0116920'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0117665'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0118980'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0120303'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0120890'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0156812'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0164181'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0207607'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0280380'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0327056'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0361127'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0373450'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0485851'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0804461'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0822849'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt0870111'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt1019454'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt1185431'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt1270798'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt12747748'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt1355683'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt1512235'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt1699509'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt1781840'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt2290075'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt3813310'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/tt5226220'),)
graph queried in 0.005481209 seconds, 41 triples
---
execute_sparql_query:
PREFIX c: <http://cosmosdb.com/imdb#>
SELECT ?o
WHERE {
    <http://cosmosdb.com/imdb/tt0087277> c:principal ?o .
}
LIMIT 100

(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0000102'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001742'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001475'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001848'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001606'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0000572'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0490855'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0329829'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0564589'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0950281'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0006889'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0705135'),)
(rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0951722'),)
graph queried in 0.001131083 seconds, 13 triples
```

---

## Run the Web Application

TODO - implement and document.  Very similar to the impl1 web app.

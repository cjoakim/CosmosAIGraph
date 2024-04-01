# CosmosAIGraph : Load Azure Cosmos DB vCore

## The Data - PyPi and NPM Libraries

The **impl1\data** directory in this repo contains a curated set of
[PyPi (Python)](https://pypi.org/) and
[NPM (JavaScript/TypeScript)](https://www.npmjs.com/) library JSON documents.

The NPM JSON files were obtained with the **npm info {libname} --json**,
command while the PyPi JSON files were obtained with HTTP requests to 
URLs such as **https://pypi.org/pypi/{libname}/json**.  Both of these
datasources are public.

This domain of software libraries was chosen because it should be
**relatable** to most customers, and it also suitable for **Bill-of-Materials**
graphs.

## Assumptions

This page assumes that you have set the following environment variables:

```
CAIG_AZURE_MONGO_VCORE_CONN_STR
CAIG_GRAPH_SOURCE_DB
CAIG_GRAPH_SOURCE_CONTAINER
CAIG_CONVERSATIONS_CONTAINER
CAIG_DOCUMENTS_CONTAINER
```

This page also assumes that the name of your database is **graph**
and the container within this database is named **libraries**.

## Loading your Cosmos DB vCore Database - library documents

Navigate to the impl1\app_console directory of this repo and execute
the following commands:

```
> .\venv.ps1                      <-- create the python virtual environment

> .\venv\Scripts\Activate.ps1     <-- activate the python virtual environment

> python main.py create_vcore_indexes 

> python main.py load_vcore_with_library_documents
```

## Verifying the Data Load

cd to the impl1 directory and run the following script:

```
> .\mongosh.ps1 vcore
```

This will open a mongo shell program connected to your vCore account.

Enter the command **use graph** to start using that database.

Then enter the command **show collections** to list the containers/collections
in that database.

Then enter the command **db.libraries.countDocuments()** to count the number
of documents in the libraries container.  **The count should be ~25k**.
If not, then the data load was not successful.

Lastly, display a random document by entering command **db.libraries.findOne()**

This sequence of commands is shown below:

```
[mongos] test>

[mongos] test> use graph
switched to db graph

[mongos] graph> show collections
cache
libraries

[mongos] graph> db.libraries.countDocuments()
28540

[mongos] graph> db.libraries.findOne()
... a random document will be displayed
```

---

## Loading your Cosmos DB vCore Database - documents for vector search

**Note: You don't need to execute this section if you don't plan on using Vector Search.**

**A significant amount of data-wrangling time and effort is required.**

### Create Standard Indexes on the non-vector attributes

In your mongo shell program excute the following three commands in your database.

```
db.documents.createIndex( { "libtype": 1 } )

db.documents.createIndex( { "libname": 1 } )

db.documents.createIndex( { "url": 1 } )
```

### Create the Vector Search Index

See https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search
for the documentation onb this index type.

In your mongo shell program excute the following command in your database.

```
db.runCommand({
  createIndexes: 'documents',
  indexes: [
    {
      name: 'vectorSearchIndex',
      key: {
        "embeddings": "cosmosSearch"
      },
      cosmosSearchOptions: {
        kind: 'vector-ivf',
        numLists: 20,
        similarity: 'COS',
        dimensions: 1536
      }
    }
  ]
});
```

### Verify the indexes in the documents container

Run the following **getIndexes()** commands in your mongo shell program.
You should see similar output to the following. 

```
db.documents.getIndexes()

{
    "v" : 2.0,
    "key" : {
        "_id" : 1.0
    },
    "name" : "_id_"
}
{
    "v" : 2.0,
    "key" : {
        "embeddings" : "cosmosSearch"
    },
    "name" : "vectorSearchIndex",
    "cosmosSearchOptions" : {
        "kind" : "vector-ivf",
        "numLists" : 20.0,
        "similarity" : "COS",
        "dimensions" : 1536.0
    }
}
{
    "v" : 2.0,
    "key" : {
        "libtype" : 1.0
    },
    "name" : "libtype_1"
}
{
    "v" : 2.0,
    "key" : {
        "libname" : 1.0
    },
    "name" : "libname_1"
}
{
    "v" : 2.0,
    "key" : {
        "url" : 1.0
    },
    "name" : "url_1"
}
```

### Prepare the document data

Navigate to directory **impl1\app_console**, and create and activate the
python by executing the **venv.ps1** script.

Then execute the following command.
**It will take several hours to run.**

```
python main.py vectorize_load_vcore_with_html_documents
```

The logic in this process involves the following:

- Iterating the JSON files in these directories
  - impl1/data/npm/html_pages/ and impl1/data/pypi/html_pages/ directories in this repo
  - These files contain the **raw HTML**, in the "html" attribute, from the URLs linked to by the library documents
  - These html_pages documents were previously created for you
  - The **httpx** library was used to fetch the raw HTML from the URLs
- For each of these JSON files the logic is:
    - Use the BeautifulSoup library to extract the text from the raw html 
    - Further minimize this extracted text - newline and redundant space characters, etc.
    - Invoke Azure OpenAI to **vectorize** (i.e. - create embeddings) from this minimized text
    - Load a document into Cosmos DB vCore with this data - libtype, libname, minimized text, and emveddings

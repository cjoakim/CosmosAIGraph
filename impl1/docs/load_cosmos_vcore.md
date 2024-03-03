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
```

This page also assumes that the name of your database is **graph**
and the container within this database is named **libraries**.

## Loading your Cosmos DB vCore Database

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

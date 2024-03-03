# readme for sparql directory

This directory contains Jinga2 templates for SPARQL RDF queries.

For example, the following is a Jinga2 template for a SPARQL query:

```
PREFIX c: <http://cosmosdb.com/caig#> 
SELECT ?used_lib
WHERE {
    <http://cosmosdb.com/caig/{{libname}}> c:uses_lib ?used_lib .
}
LIMIT {{limit}}
```

The values within the {{ and }} characters are replaced at runtime.
See file **app/pysrc/util/sparql_template.py** in this repo.

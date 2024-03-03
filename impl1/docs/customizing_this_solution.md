# CosmosAIGraph : Customizing this Solution

This page strives to guide the reader in implementing their
own application, based on CosmosAIGraph, with their own data.

This list of steps was useful in the development of CosmosAIGraph itself,
and customers are recommended to take similar steps.

## Step 1: Define your Requirements

It is essential to start here.  Define your primary requirements.
Specifically, define the list of graph queries in your application.
Put these into a list to identify each one by a shortname (i.e. - q1, 2, etc.).

Use of the [CQRS](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs)
pattern is very useful here.

## Step 2: Survey your Data

Ask the question: "Does the data that I have available enable the answering
of these graph/knowledge-graph queries?".

If so, proceed.  If not, revisit the requirements and/or data sources.

## Step 3: Understand RDF graph technology, Ontologies, and SPARQL

RDF technology uses the beautifully simple concept of **triples**.
Each triple consists of a subject, predicate, and object.
A RDF database is simply an Ontology (i.e. - schema) with
an array of many triples.

Though it's an old book, this O'Reilly book was very useful in learning RDF,
OWL, and SPARQL at the beginning of the development of CosmosAIGraph:
https://www.oreilly.com/library/view/learning-sparql/9781449311285/

Other learning sources include the following from the **W3C**:

- https://www.w3.org/RDF/
- https://www.w3.org/TR/owl2-rdf-based-semantics/
- https://www.w3.org/TR/sparql11-query/

## Step 4: Create your initial Web Ontology

Based on your requirements and data, create your own *.owl file.
Define the classes and relationships pertinent to your system.

See file **impl1/app_graph/ontologies/libraries.owl** as a reference.

The owl file development process should be iterative.

## Step 5: Create a Data-Wrangling process to populate an rdflib graph

Given your datasets, and your evolving OWL file, populate 
an in-memory rdflib graph, then serialize it to a *.nt file.

Write a console application to load your graph from the OWL and nt
file, and craft SPARQL queries that seek to answer the queries you
identified in Step 1.

You may need to implement programming logic to execute multiple SPARQL
queries to satisfy an individual use-case requirement.

Expect steps 4 and 5 to be iterative.  Modify your OWL, refactor
your data-wrangling process, and recreate your rdflib graph and nt file.

## Step 6: Create a minimal "SPARQL QUERY" web interface

Only after you have a reasonably working graph and ontology should
you try to port it to a web application.

It is recommended that you implement your own "SPARQL Query" UI, 
similar to the CosmosAIGraph implementation, so that you can
further explore and iterate your OWL and graph.

## Step 7: Create your web application UI

Once your OWL and graph design is stabilized, implement your desired UI.

This may include graph visualizations.  This reference application
uses the [D3.js](https://d3js.org/) JavaScript library for visualizations, but of course
you may use any libraries you prefer.


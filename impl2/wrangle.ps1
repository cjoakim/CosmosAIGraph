#!/bin/bash

# Wrangle the IMDb TSV data into RDF Graph Data.
# It is assumed that the python virtual environment has been created
# and activated before executing this script.
# Chris Joakim, Microsoft

# delete the output files
del data\*.json

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

echo 'done'

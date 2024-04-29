"""
Usage:
    python wrangle.py explore_imdb_tsv_files > docs/tsv_file_info.txt
    python wrangle.py step0_print_criteria
    python wrangle.py step1_filter_ratings
    python wrangle.py step2_filter_titles
    python wrangle.py step3_gather_names
    python wrangle.py step4_gather_principals
    python wrangle.py step5_print_selected_entities
    python wrangle.py step6_build_rdf_triples
    python wrangle.py step10_load_rdflib_graph
Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import json
import os
import sys
import time
import logging
import traceback


from docopt import docopt
from dotenv import load_dotenv

import rdflib

from rdflib import Graph, Literal, RDF, URIRef, BNode
from rdflib.namespace import Namespace, NamespaceManager

from rdflib.extras.infixowl import AllClasses, AllProperties, GetIdentifiedClasses


from pysrc.util.counter import Counter
from pysrc.util.fs import FS


# Inclusion/Exclusion Parameters and Filenames:
MIN_RATING = 6.0
MIN_YEAR = 1980
MIN_MINUTES = 75
ROLES = "actor,actress,director,producer".split(",")
RATINGS_FILE = "data/ratings.json"
TITLES_FILE = "data/titles.json"
NAMES_FILE = "data/names.json"
RDF_NT_FILE = "rdf/imdb.nt"
RDF_NT_SER_FILE = "tmp/imdb_ser.nt"
NAMES_FILTERED_FILE = "data/names_filtered.json"

def print_options(msg):
    print(msg)
    arguments = docopt(__doc__, version="1.0.0")
    print(arguments)

def explore_imdb_tsv_files():
    """ read and understand the format of the raw IMDb TSV files """
    print("explore_imdb_tsv_files") 
    tsv_files = [
        "name.basics.tsv",
        "title.basics.tsv",
        "title.principals.tsv",
        "title.ratings.tsv"
    ]
    for basename in tsv_files:
        filename = "data/{}".format(basename)
        linenum = 0
        with open(file=filename, encoding="utf-8", mode="rt") as file:
            print("--- {} ---".format(filename))
            for line in file:
                linenum = linenum + 1
                if linenum < 4:
                    tokens = line.strip().split("\t")
                    print("{} tokens in line {}: {}".format(len(tokens), linenum, tokens))
                    print(line)
            print("file {} has {} lines".format(filename, linenum))
    # file data/name.basics.tsv      13,442,835 lines
    # file data/title.basics.tsv     10,725,210 lines
    # file data/title.principals.tsv 85,403,798 lines
    # file data/title.ratings.tsv     1,430,468 lines

def step0_print_criteria():
    print("Selection Criteria:")
    print("  MIN_RATING:  {}".format(MIN_RATING))
    print("  MIN_YEAR:    {}".format(MIN_YEAR))
    print("  MIN_MINUTES: {}".format(MIN_MINUTES))
    print("  ROLES:       {}".format(ROLES))

def step1_filter_ratings():
    """
    Exclude the titles with a rating less than MIN_RATING.
    Create the RATINGS_FILE.
    """
    filename, linenum = "data/title.ratings.tsv", 0
    excluded_count = 0
    c = Counter()
    ratings_dict = dict()
    with open(file=filename, encoding="utf-8", mode="rt") as file:
        for line in file:
            linenum = linenum + 1
            if (linenum > 1):
                # ['tconst', 'averageRating', 'numVotes']
                tokens = line.strip().split("\t")
                tconst = tokens[0].strip()
                rating = float(tokens[1].strip())
                if rating >= MIN_RATING:
                    ratings_dict[tconst] = rating
                else:
                    excluded_count = excluded_count + 1
                c.increment(str(rating))

    print("included count: {}".format(len(ratings_dict)))
    print("excluded count: {}".format(excluded_count))
    write_json(c.get_data(), "data/ratings_counted.json", True)
    write_json(ratings_dict, RATINGS_FILE, True)

def step2_filter_titles():
    """
    Exclude adult titles, low-rated titles, titles created before MIN_YEAR, 
    and titles less than MIN_MINUTES long.
    Create the TITLES_FILE.
    """
    filename, linenum = "data/title.basics.tsv", 0
    ratings = load_ratings()
    ratings_keys = ratings.keys()
    c = Counter()
    titles_dict = dict()
    excluded_count = 0
    with open(file=filename, encoding="utf-8", mode="rt") as file:
        for line in file:
            linenum = linenum + 1
            if (linenum > 1):
                #      0          1              2               3             4           5           6           7                8
                # ['tconst', 'titleType', 'primaryTitle', 'originalTitle', 'isAdult', 'startYear', 'endYear', 'runtimeMinutes', 'genres']
                tokens = line.strip().split("\t")
                tconst = tokens[0].strip()
                ttype  = tokens[1].strip().lower()
                title  = tokens[2].strip().lower()
                adult  = int_value(tokens[4].strip(), 1)
                year   = int_value(tokens[5].strip(), 0)
                minutes = int_value(tokens[7].strip(), 0)
                genres = tokens[8].strip().lower().split(",")
                ttype_key = "ttype {}".format(ttype)
                adult_key = "adult {}".format(adult)
                year_key  = "year {}".format(year)
                genre_key = "genre {}".format(genres)
                c.increment(ttype_key)
                c.increment(adult_key)
                c.increment(year_key)
                c.increment(genre_key)
                if tconst in ratings_keys:
                    if (adult == 0) and (year >= MIN_YEAR) and (minutes >= MIN_MINUTES):
                        d = dict()
                        d['tconst'] = tconst
                        d['title'] = title
                        d['year'] = year
                        d['rating'] = ratings[tconst]
                        d['genres'] = genres
                        d['principals'] = dict()
                        titles_dict[tconst] = d
                    else:
                        excluded_count = excluded_count + 1
                else:
                    excluded_count = excluded_count + 1

    print("included count: {}".format(len(titles_dict)))
    print("excluded count: {}".format(excluded_count))
    write_json(c.get_data(), "data/titles_counted.json", True)
    write_json(titles_dict, TITLES_FILE, False)

def step3_gather_names():
    """
    Read the names TSV file, create the unfiltered NAMES_FILE.
    """
    filename, linenum = "data/name.basics.tsv", 0
    names_dict = dict()
    with open(file=filename, encoding="utf-8", mode="rt") as file:
        for line in file:
            linenum = linenum + 1
            if (linenum > 1):
                # ['nconst', 'primaryName', 'birthYear', 'deathYear', 'primaryProfession', 'knownForTitles']
                # ['nm0000001', 'Fred Astaire', '1899', '1987', 'actor,miscellaneous,producer', 'tt0072308,tt0050419,tt0053137,tt0027125']
                tokens = line.strip().split("\t")
                nconst = tokens[0].strip()
                d = dict()
                d['nconst'] = nconst
                d['name'] = tokens[1].strip() 
                d['born'] = int_value(tokens[2].strip(), -1)
                d['died'] = int_value(tokens[3].strip(), -1)
                d['titles'] = dict()  # exclude later if in zero movies
                names_dict[nconst] = d
    write_json(names_dict, NAMES_FILE, False)

def step4_gather_principals():
    """
    Read the principals TSV file and update both the titles objects and the names objects.
    Remove from the names dict any names that are in none of these selected titles.
    Read and save the updated TITLES_FILE.
    Read the NAMES_FILE save the updated and filtered NAMES_FILTERED_FILE.
    """
    filename, linenum = "data/title.principals.tsv", 0
    titles = load_titles()
    names = load_names()
    titles_keys = titles.keys()
    names_keys = names.keys()
    
    excluded_titles_count, excluded_names_count = 0, 0
    with open(file=filename, encoding="utf-8", mode="rt") as file:
        for line in file:
            linenum = linenum + 1
            if linenum > 1:
                #     0          1           2          3
                # ['tconst', 'ordering', 'nconst', 'category', 'job', 'characters\n']
                # ['tt0000001', '1', 'nm1588970', 'self', '\\N', '["Self"]\n']
                # ['tt0000001', '2', 'nm0005690', 'director', '\\N', '\\N\n']
                # ['tt0000001', '3', 'nm0005690', 'producer', 'producer', '\\N\n']
                if (linenum % 100000) == 0:
                    print("processing principal line {}".format(linenum))
                tokens = line.split("\t")
                tconst = tokens[0].strip()
                if (tconst in titles_keys):
                    title = titles[tconst]
                    nconst = tokens[2].strip().lower()
                    role = tokens[3].strip().lower() 
                    if role in ROLES:
                        title['principals'][nconst] = role
                        print("updated title {} with {} in role {}".format(tconst, nconst, role))
                        if nconst in names_keys:
                            n = names[nconst]
                            if tconst in n["titles"]:
                                pass  # already there; dual roles such as actor,director
                            else:
                                n["titles"][tconst] = role
                                print("updated name {} in {} with role {}".format(nconst, tconst, role))
                else:
                    excluded_titles_count = excluded_titles_count + 1

    # remove the names that are in none of these filtered titles
    names_to_delete = list()
    for nconst in names_keys:
        n = names[nconst]
        if len(n["titles"].keys()) == 0:
            names_to_delete.append(nconst)
    for nconst in names_to_delete:
        del names[nconst]
        excluded_names_count = excluded_names_count + 1

    print("excluded titles count: {}".format(excluded_titles_count))
    print("excluded names count:  {}".format(excluded_names_count))
    write_json(titles, TITLES_FILE, False)
    write_json(names, NAMES_FILTERED_FILE, False)

def step5_print_selected_entities():
    names = load_names_filtered()
    titles = load_titles()
    print("names count:  {}".format(len(names.keys())))
    print("titles count: {}".format(len(titles.keys())))
    # fred astaire    = nm0000001
    # lauren bacall   = nm0000002
    # kevin bacon     = nm0000102
    # lori singer     = nm0001742
    # kevin costner   = nm0000126
    # footloose       = tt0087277
    # field of dreams = tt0097351
    names_of_interest = "nm0000001,nm0000002,nm0000102,nm0001742,nm0000126".split(",")
    titles_of_interest = "tt0087277,tt0097351".split(",")

    for nconst in names_of_interest:
        print("---")
        if nconst in names.keys():
            obj = names[nconst]
            print(json.dumps(obj, sort_keys=False, indent=2))
        else:
            print("{} not found".format(nconst))

    for tconst in titles_of_interest:
        print("---")
        if tconst in titles.keys():
            obj = titles[tconst]
            print(json.dumps(obj, sort_keys=False, indent=2))
        else:
            print("{} not found".format(nconst))

def step6_build_rdf_triples():
    names = load_names_filtered()
    titles = load_titles()
    names_keys = names.keys()
    titles_keys = titles.keys()

    lines = list()

    for tconst in titles_keys:
        t = titles[tconst]
        lines.append(triple(tconst, "TYPE", "Movie", False))
        lines.append(triple(tconst, "title", t["title"], True))
        lines.append(triple(tconst, "year", t["year"], True))
        lines.append(triple(tconst, "rating", t["rating"], True))
        for g in t["genres"]:
            lines.append(triple(tconst, "genre", g, True))
        for p in t["principals"].keys():
            r = t["principals"][p]
            #lines.append(triple(tconst, r, p))
            lines.append(triple(tconst, "has_principal", p, False))

        # {
        #   "tconst": "tt0097351",
        #   "title": "field of dreams",
        #   "year": 1989,
        #   "rating": 7.5,
        #   "genres": [
        #     "drama",
        #     "family",
        #     "fantasy"
        #   ],
        #   "principals": {
        #     "nm0000126": "actor",
        #     "nm0000469": "actor",
        #     "nm0000501": "actor",
        #     "nm0001496": "actress",
        #     "nm0000451": "actress",
        #     "nm0124079": "actor",
        #     "nm0000044": "actor",
        #     "nm0001844": "actor",
        #     "nm0113474": "actor",
        #     "nm0025908": "actor",
        #     "nm0004675": "director",
        #     "nm0330077": "producer",
        #     "nm0330379": "producer"
        #   }
        # }

    for nconst in names_keys:
        n = names[nconst]
        lines.append(triple(nconst, "TYPE", "Person", False))
        lines.append(triple(nconst, "person_name", n["name"], True))
        lines.append(triple(nconst, "person_born", n["born"], True))
        lines.append(triple(nconst, "person_died", n["died"], True))
        for t in n["titles"].keys():
            r = n["titles"][t]
            lines.append(triple(nconst, "in_movie", t, False))

        # {
        #   "nconst": "nm0001742",
        #   "name": "Lori Singer",
        #   "born": -1,
        #   "died": -1,
        #   "titles": {
        #     "tt0086991": "actress",
        #     "tt0087277": "actress",
        #     "tt0090209": "actress",
        #     "tt0098622": "actress",
        #     "tt19388530": "actress"
        #   }
        # }

    print("line count: {}".format(len(lines)))
    FS.write_lines(lines, RDF_NT_FILE)

def step10_load_rdflib_graph():
    cwd = os.getcwd()
    owl_file = "{}{}{}".format(cwd, os.sep, "ontologies/imdb.owl")
    triples_file = "{}{}{}".format(cwd, os.sep, RDF_NT_FILE)
    serialized_file = "{}{}{}".format(cwd, os.sep, RDF_NT_SER_FILE)
    print(owl_file)
    print(triples_file)
    print(serialized_file)
    custom_namespace = "http://cosmosdb.com/imdb#"

    CNS = Namespace(custom_namespace)  # CNS ~ Custom Namespace
    print("parsing owl_file")
    t1 = time.perf_counter()
    g = Graph()
    g.bind("c", CNS)
    g.parse(owl_file, format="xml")
    print(g)
    print("parsing triples_file")
    g.parse(triples_file, format="nt")
    t2 = time.perf_counter()
    seconds = f"{(t2 - t1):.9f}"
    print("graph loaded in {} seconds".format(seconds))

    t1 = time.perf_counter()
    g.serialize(format="nt", destination=serialized_file, encoding="utf-8")
    t2 = time.perf_counter()
    print("graph serialize in {} seconds".format(seconds))

    count = 0
    t1 = time.perf_counter()
    for s, p, o in g:  # Iterate the graph, counting the triples
        count = count + 1
    t2 = time.perf_counter()
    seconds = f"{(t2 - t1):.9f}"
    print("graph iterated in {} seconds, {} triples".format(seconds, count))
    
    t1 = time.perf_counter()
    sparql = sparql_footloose_principals_query()
    rows = list()
    for row in g.query(sparql):
        print(row)
        rows.append(row)
    t2 = time.perf_counter()
    seconds = f"{(t2 - t1):.9f}"
    print("graph queried in {} seconds, {} triples".format(seconds, len(rows)))
    
    # output:
    # parsing triples_file
    # graph loaded in 64.787656416 seconds
    # graph serialize in 64.787656416 seconds
    # graph iterated in 3.938760041 seconds, 5721065 triples
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0000102'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001742'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001475'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001848'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0001606'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0000572'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0490855'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0329829'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0564589'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0950281'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0006889'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0705135'),)
    # (rdflib.term.URIRef('http://cosmosdb.com/imdb/nm0951722'),)
    # graph queried in 0.051442875 seconds, 13 triples

    # the footloose movie:
    # {
    # "tconst": "tt0087277",
    # "title": "footloose",
    # "principals": {
    #     "nm0000102": "actor",
    #     "nm0001742": "actress",
    #     "nm0001475": "actor",
    #     "nm0001848": "actress",
    #     "nm0001606": "actor",
    #     "nm0000572": "actress",
    #     "nm0490855": "actor",
    #     "nm0329829": "actress",
    #     "nm0564589": "actress",
    #     "nm0950281": "actor",
    #     "nm0006889": "director",
    #     "nm0705135": "producer",
    #     "nm0951722": "producer"
    # }
    # }

def sparql_footloose_principals_query():
    return """
PREFIX c: <http://cosmosdb.com/imdb#> 
SELECT ?o
WHERE {
    <http://cosmosdb.com/imdb/tt0087277> c:principal ?o .
}
LIMIT 100
""".strip()

def triple(subject, predicate, object, literal: bool):
    p, o = "", ""
    s = "<http://cosmosdb.com/imdb/{}>".format(subject)

    if predicate == "TYPE":
        p = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
    else:
        p = "<http://cosmosdb.com/imdb#{}>".format(predicate)

    if literal == True:
        if isinstance(object, str):
            lit = str(object).replace('"','')
            o = '"{}"'.format(lit)
        else:
            o = '"{}"'.format(object)
    else:
        if predicate == "TYPE":
            o = "<http://cosmosdb.com/imdb#{}>".format(object) 
        else:
            o = "<http://cosmosdb.com/imdb/{}>".format(object)

    return "{} {} {} .".format(s, p, o)

def int_value(s, default_value):
    try:
        return int(s)
    except:
        return default_value
    
def load_ratings() -> dict:
    data = FS.read_json(RATINGS_FILE)
    print("load_ratings, len: {}".format(len(data)))
    return data

def load_titles() -> dict:
    data = FS.read_json(TITLES_FILE)
    print("load_titles, len: {}".format(len(data)))
    return data

def load_names() -> dict:
    data = FS.read_json(NAMES_FILE)
    print("load_names, len: {}".format(len(data)))
    return data

def load_names_filtered() -> dict:
    data = FS.read_json(NAMES_FILTERED_FILE)
    print("load_names_filtered, len: {}".format(len(data)))
    return data

def write_json(data, outfile, sort=False):
    jstr = json.dumps(data, sort_keys=sort, indent=2)
    with open(file=outfile, encoding="utf-8", mode="w") as file:
        file.write(jstr)
        print("file written: {}, len: {}".format(outfile, len(data)))
              

if __name__ == "__main__":
    # standard initialization of env and logger
    load_dotenv(override=True)
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
    if len(sys.argv) < 2:
        print_options("Error: invalid command-line")
        exit(1)
    else:
        try:
            func = sys.argv[1].lower()
            if func == "explore_imdb_tsv_files":
                explore_imdb_tsv_files()
            elif func == "step0_print_criteria":
                step0_print_criteria()
            elif func == "step1_filter_ratings":
                step1_filter_ratings()
            elif func == "step2_filter_titles":
                step2_filter_titles()
            elif func == "step3_gather_names":
                step3_gather_names()
            elif func == "step4_gather_principals":
                step4_gather_principals()
            elif func == "step5_print_selected_entities":
                step5_print_selected_entities()
            elif func == "step6_build_rdf_triples":
                step6_build_rdf_triples()
            elif func == "step10_load_rdflib_graph":
                step10_load_rdflib_graph()
            else:
                print_options("Error: invalid function: {}".format(func))
        except Exception as e:
            logging.info(str(e))
            logging.info(traceback.format_exc())

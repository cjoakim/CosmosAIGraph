"""
This module is for ad-hoc tasks not related to the actual working app.
Usage:
    python main.py list_defined_env_vars
    python main.py load_vcore_with_library_documents
    python main.py create_vcore_indexes
    python main.py gather_html_urls_from_docs
    python main.py fetch_html_urls
    python main.py vectorize_load_vcore_with_html_documents
Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import json
import sys
import time
import logging
import os
import psutil
import traceback

import httpx
import tiktoken

from bs4 import BeautifulSoup

from docopt import docopt
from dotenv import load_dotenv

from pysrc.services.ai_service import AiService
from pysrc.services.config_service import ConfigService
from pysrc.services.cosmos_vcore_service import CosmosVCoreService
from pysrc.util.fs import FS


def print_options(msg):
    print(msg)
    arguments = docopt(__doc__, version="1.0.0")
    print(arguments)


def list_defined_env_vars():
    env_var_names = sorted(ConfigService.defined_environment_variables().keys())
    for name in env_var_names:
        value = ConfigService.envvar(name)
        logging.info("{}: {}".format(name, value))


def connect_to_vcore_graph_source():
    """
    connect to the vcore account, and return a 3-tuple of
    (vcore, dbname, cname), where vcore is an instance of
    class CosmosVCoreService.
    """
    opts = dict()
    opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
    vcore = CosmosVCoreService(opts)
    if "pymongo.mongo_client.MongoClient" in str(type(vcore.get_client())):
        logging.info("connected to vcore")
    else:
        logging.info("unable to connect to vcore; exiting")
        return
    dbname = ConfigService.graph_source_db()
    cname = ConfigService.graph_source_container()
    vcore.set_db(dbname)
    vcore.set_coll(cname)
    return (vcore, dbname, cname)


def load_vcore_with_library_documents():
    vcore, dbname, cname = connect_to_vcore_graph_source()
    logging.info("using vcore db: {}, collection: {}".format(dbname, cname))
    pause_seconds = 10
    logging.info(
        "pausing {} seconds before loading the documents...".format(pause_seconds)
    )
    time.sleep(pause_seconds)
    max_load_idx = 999999
    load_docs_from_directory(vcore, max_load_idx, "../data/npm/wrangled_libs")
    load_docs_from_directory(vcore, max_load_idx, "../data/pypi/wrangled_libs")


def load_docs_from_directory(vcore, max_load_idx, wrangled_libs_dir):
    files_list = FS.list_files_in_dir(wrangled_libs_dir)
    filtered_files_list = filter_files_list(files_list, ".json")
    max_idx = len(filtered_files_list) - 1
    for idx, filename in enumerate(filtered_files_list):
        fq_name = "{}/{}".format(wrangled_libs_dir, filename)
        if fq_name.endswith(".json"):
            if idx < max_load_idx:
                try:
                    logging.info(
                        "processing {} of {}: {}".format(idx, max_idx, fq_name)
                    )
                    doc = FS.read_json(fq_name)
                    vcore.insert_doc(doc)
                except Exception as e:
                    logging.info("error processing {}: {}".format(fq_name, str(e)))
                    continue


def filter_files_list(files_list, suffix):
    filtered = list()
    for f in files_list:
        if f.endswith(suffix):
            filtered.append(f)
    return filtered


def create_vcore_indexes():
    vcore, dbname, cname = connect_to_vcore_graph_source()
    logging.info("using vcore db: {}, collection: {}".format(dbname, cname))

    indexes = vcore.get_coll_indexes(cname)
    logging.info(
        "indexes before:\n{}".format(json.dumps(indexes, sort_keys=False, indent=2))
    )

    vcore.create_simple_index("libtype")
    vcore.create_simple_index("name")
    vcore.create_simple_index("id")

    indexes = vcore.get_coll_indexes(cname)
    logging.info(
        "indexes after:\n{}".format(json.dumps(indexes, sort_keys=False, indent=2))
    )

    # cache container
    cname = "cache"
    vcore.set_db(dbname)
    vcore.set_coll(cname)
    logging.info("using vcore db: {}, collection: {}".format(dbname, cname))
    vcore.create_simple_index("cache_key")
    indexes = vcore.get_coll_indexes(cname)
    logging.info(
        "indexes after:\n{}".format(json.dumps(indexes, sort_keys=False, indent=2))
    )


def fetch_vectorize_urls():
    logging.info("fetch_vectorize_urls")
    urls = gather_urls_from_docs()
    logging.info("urls count: {}".format(len(urls.keys())))
    FS.write_json(urls, "../data/urls.json")


def gather_html_urls_from_docs():
    """
    Extract the homepage and other http urls from the library documents.
    This implementation uses the JSON documents on disk in this repo,
    but you could alternatively read them from the vcore database.
    Save the gathered URLs to file ../data/html_urls.json.
    """
    urls = dict()
    wrangled_libs_dirs = ["../data/npm/wrangled_libs", "../data/pypi/wrangled_libs"]

    for dir in wrangled_libs_dirs:
        libtype = "npm"
        if "pypi" in dir:
            libtype = "pypi"
        files = FS.list_files_in_dir(dir)
        for file in files:
            try:
                fq_name = "{}/{}".format(dir, file)
                logging.info("gathering urls from {}".format(fq_name))
                doc = FS.read_json(fq_name)
                libname = doc["name"]
                if "homepage" in doc.keys():
                    url = str(doc["homepage"]).strip()
                    if url.startswith("http") and len(url) > 10:
                        urls[url] = [libtype, libname]
                if "npm" in dir:
                    url = "https://www.npmjs.com/package/{}".format(doc["name"])
                else:
                    if "package_url" in doc.keys():
                        url = str(doc["package_url"]).strip()
                        if url.startswith("http") and len(url) > 10:
                            urls[url] = [libtype, libname]
            except Exception as e:
                logging.info("error reading {}: {}".format(fq_name, str(e)))
                continue
    FS.write_json(urls, "../data/html_urls.json")


def fetch_html_urls():
    data = FS.read_json("../data/html_urls.json")
    max_urls = 999999
    for idx, url in enumerate(sorted(data.keys())):
        if idx < max_urls:
            try:
                libtype, libname = data[url][0], data[url][1]
                logging.info("fetching: {} {}".format(idx, url))
                r = httpx.get(url, follow_redirects=True)
                logging.info(r)
                html = r.text
                outfile = html_info_filename(libtype, libname, idx)
                info_doc = dict()
                info_doc["libtype"] = libtype
                info_doc["libname"] = libname
                info_doc["url"] = url
                info_doc["html"] = normalize_html(html)
                info_doc["embeddings"] = list()
                FS.write_json(info_doc, outfile)
            except Exception as e:
                logging.info("error on url {}".format(url))
                continue


def normalize_html(html):
    return html.replace("\n", "").replace("\r", "").replace("\t", "").strip()


def html_info_filename(libtype, libname, idx):
    try:
        if libtype == "npm":
            dir = "../data/npm/html_pages"
            return "{}/{}_{}_{}.json".format(dir, libtype, libname, idx)
        else:
            dir = "../data/pypi/html_pages"
            return "{}/{}_{}_{}.json".format(dir, libtype, libname, idx)
    except Exception as e:
        logging.info("error in html_filename: {} {}".format(url, str(e)))
        return None


def vectorize_load_vcore_with_html_documents():
    html_dirs = ["../data/pypi/html_pages", "../data/npm/html_pages"]
    ai_svc = AiService()
    aoai_client = ai_svc.aoai_client
    vcore, dbname, cname = connect_to_vcore_graph_source()
    vcore.set_coll(ConfigService.documents_container())

    for dir in html_dirs:
        files_list = FS.list_files_in_dir(dir)
        for idx, filename in enumerate(files_list):
            if idx < 999999:
                if filename.endswith(".json"):
                    try:
                        logging.info("========== processing: {}".format(filename))
                        fq_name = "{}/{}".format(dir, filename)
                        logging.info(fq_name)
                        # doc has the keys: ['libtype', 'libname', 'url', 'html', 'embeddings']
                        doc = FS.read_json(fq_name)
                        html = doc["html"]
                        if html is not None:
                            soup = BeautifulSoup(html, "html.parser")
                            html_text = soup.get_text()
                            doc["text"] = minimize_text(html_text, doc["url"])
                            doc["html_length"] = len(html)
                            doc["text_length"] = len(doc["text"])
                            del doc["html"]  # don't need the html anymore
                            resp = ai_svc.generate_embeddings(doc["text"])
                            doc["embeddings"] = resp.data[0].embedding
                            FS.write_json(doc, "tmp/{}".format(filename))
                            vcore.insert_doc(doc)
                            time.sleep(1.0)
                    except Exception as e:
                        logging.info(
                            "error in vectorize_load_vcore_with_html_documents: {} {}".format(
                                filename, str(e)
                            )
                        )
                        continue


def minimize_text(html_text, url):
    s = html_text.replace("\n", "").replace("\r", "").replace("\t", "")
    for n in range(10):
        s = s.replace("  ", " ")
    logging.info("minimize_text: {} {} {}".format(len(html_text), len(s), url))

    # This error is apt to happen with large text strings passed to create embeddings:
    #   "This model's maximum context length is 8191 tokens, however you requested 8329 tokens
    # One token generally corresponds to ~4 characters of text for common English text.
    # 8191 * 3 = 24,573, so conservatively truncate to 24000 characters.
    if len(s) > 24000:
        s = s[:24000].strip()
        logging.info("minimize_text: truncated to 24000 characters")
    else:
        return s.strip()


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
            if func == "list_defined_env_vars":
                list_defined_env_vars()
            elif func == "load_vcore_with_library_documents":
                load_vcore_with_library_documents()
            elif func == "create_vcore_indexes":
                create_vcore_indexes()
            elif func == "gather_html_urls_from_docs":
                gather_html_urls_from_docs()
            elif func == "fetch_html_urls":
                fetch_html_urls()
            elif func == "vectorize_load_vcore_with_html_documents":
                vectorize_load_vcore_with_html_documents()
            else:
                print_options("Error: invalid function: {}".format(func))
        except Exception as e:
            logging.info(str(e))
            logging.info(traceback.format_exc())

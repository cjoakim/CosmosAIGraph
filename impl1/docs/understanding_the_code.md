# CosmosAIGraph : Understanding the Code

This page strives to guide the reader in understanding both
the structure and implementation of this codebase.  Not every
python module is described here, only the most important ones.

Again, this is simply a **reference application** that you may
wish to refer to as you design and implement your own solitions.
Please feel free to use any part of this design and implementation,
or none.

## The app_common directory

This is where the common and reusable code for implementation is developed and tested.
Much of it is copied to the two microservice directories 
(i.e. - app_web and app_graph) as well as the other 
sub-applications (i.e - app_console) in an automated manner.

See script **impl1\app_common\deploy_master_code.xml** which uses
**Apache Ant** to deploy the code from app_common to the other subprojects.

Unit tests are in the **impl1\app_common\tests** directory.
These use the [pytest](https://pypi.org/project/pytest/) library.
Test code coverage reports are created using the [pytest-cov](https://pypi.org/project/pytest-cov/)
library. 

See the **tests.ps1** and **tests.sh** scripts in the impl1\app_common directory.

The output of the tests looks like the following:

<p align="center">
  <img src="img/pytest_unit_tests.png" width="90%">
</p>

### impl1\app_common\pysrc\models directory

File **webservice_models.py** contains the several **Pydantic models** 
that define both the request and response payloads for the web endpoints
in this application.

Likewise, **internal_models.py** implements Pydantic Models used to
describe datastructures passed between classes in the application.

### impl1\app_common\pysrc\services directory

The classes here define the **business service** logic used by the application.

**config_service.py** implements class **ConfigService** that is used by
the application for all configuration values.  "Hard-coding" of these
values is generally not done in this codebase.  It is a goal of this
reference implementation to expose as much functionality via configuration
and environment variables as possible.

**ConfigService** uses **environment variables** and this is well-suited for
**Docker** containerized applications that are deployed to environments such as 
**Azure Container Apps (ACA)** and **Azure Kubernetes Service (AKS)**.

The [python-dotenv](https://pypi.org/project/python-dotenv/) python library
is used in the codebase to optionally get environment variables via the **.env**
file.  The **.env** should not be stored in your source-control system, as
it may contain application secrets.

See the source code of this module; it lists all of the possible environment
variables used in the codebase.  They all begin with **CAIG_**.

**logging_level_service.py** defines the logic for returning a standard-library
logging level such as logging.DEBUG, logging.INFO, etc, per the environment
variable CAIG_LOG_LEVEL.  This solution uses the **logging** standard library
rather than print statements.

**ai_service.py** implements class **AiService** for all Azure OpenAI and semantic-kernel
logic.  You are certainly free to use other orchestrators, such as **LangChain**.
We chose **semantic-kernel** because the SDK was simpler and more stable.

The **generate_sparql_from_user_prompt** method in this module is where
the Azure OpenAI service is invoked to generate a SPARQL query from a
given OWL ontology and user prompt.

A primary method of **AiService** is **invoke_kernel** which generates a
LLM completion and adds it to a user conversation.  These are instances of
classes **AiCompletion** and **AiConversation**, respectively.

**AiConversation**, in **ai_conversation.py** stores the conversational state
of a given user conversation and contains the complete set of prompts, completions 
(with token usage), history, as well as any user feedback.
These conversations are persisted as JSON in the conversations container in Cosmos DB,
and thus can be used for analysis of the performance of your AI application.

The app_common directory contains file **conversation.py** that can be used
to execute a conversation, with list of user natural language, directly from
a terminal command-line rather than from the web application UI.
Modifying and using conversation.py may accelerated your development process.

**cache_service.py** implements all (optional) caching of results such as SPARQL queries.
Cosmos DB is used as the implementation of the cache.

**cosmos_vcore_service.py** provides CRUD access to the Cosmos DB Mongo vCore database,
including **vector search**.

**graph_builder.py** implements class **GraphBuilder** which utilizes the builder
pattern to create an instance of class **GraphService**, which contains an in-memory
**rdflib** database.  The source data for building the graph are JSON documents
in Cosmos DB.  One Cosmos DB document may result in several **triples** being
loaded into the in-memory graph.

Alternatively, for dev/test environments, GraphBuilder can instantiate the
in-memory graph by reading a **RDF *.nt** text file.

These environment variables are used in building the in-memory rdflib graph:
- CAIG_GRAPH_SOURCE_TYPE
- CAIG_GRAPH_SOURCE_OWL_FILENAME
- CAIG_GRAPH_SOURCE_RDF_FILENAME
- CAIG_GRAPH_SOURCE_DB
- CAIG_GRAPH_SOURCE_CONTAINER
- CAIG_AZURE_MONGO_VCORE_CONN_STR 

Please see the [Environment Variables](environment_variables.md) page where
these are described.

Please take a close look at graph_builder.py to see how the in-memory
rdflib graph is populated.  One approach uses an **RDF triples file** (i.e. - *.nt)
while the other loads the graph from **Cosmos DB** documents.

Note that [code generation](code_generation.md) may be used to generate 
a separate class named **RdflibTriplesBuilder** that is used by class
GraphBuilder in **graph_builder.py** to actually load the rdflib graph.

**graph_service.py** implements class **GraphService** which provides an interface
to all rdflib functionality including SPARQL queries.  The **in-memory rdflib graph**
is mutable.  Since it resides in-memory, rather than on disk, it results in
low-latency queries.

**entities_service.py** implements class **EntitiesService** which allows you
to define the names of the entities in your system, and thus identify them in
user natural-language.

**strategy_builder.py** implements class **StrategyBuilder** used to determine
the **strategy** to be used in obtaining RAG data.  The currently identified
strategies are: **db, graph, and vector**.  This class uses EntitiesService.

**rag_data_service.py** implements class **RAGDataService** which is used to fetch
the pertinent RAG data given a user utterance or natural-language.
This class uses StrategyBuilder to determine the appropriate strategy to use
when fetching the RAG data.  The RAG data can be read directly from 
Cosmos DB if the stragegy is "db", otherwise either an in-memory RDF graph
query or a Cosmos DB vector search is used to identify and fetch the RAG data.

**rag_data_result.py** implements class **RAGDataResult**.  Instances of this class
are returned by the **get_rag_data** method of the above class RAGDataService.

### impl1\app_common\pysrc\util directory

**fs.py** provides methods for accessing the local filesystem.

**owl_formatter.py** is used to return a minimized version of
a given OWL file content in order to be passed efficiently in an
AzureOpenAI system prompt.

**prompts.py** is used to define system and user prompts for 
Azure OpenAI.  This module is expected to evolve as the codebase
adds more semantic-kernel functionality.

**prompt_optimizer.py** implements class **PromptOptimizer** which is used
in class **AiService** to optimize/truncate the conversation context
and history so as to fit within a given Azure OpenAI **max_tokens** value.

PromptOptimizer also generates a high-fidelity prompt text value that can 
be stored in the AiConversation and displayed in the UI. Both semantic-kernel
and LangChain seem to do a poor job of exposing the actual merged prompt text
used with invoking the LLM.

**sparql_formatter.py** is used to return 'pretty' version of
a given (AI-generated) SPARQL query.

**sparql_template.py** is used render dynamic SPARQL queries from jinja2
templates and a dictionary of values.

**owl_sax_handler.py** implements class **OwlSaxHandler** which can be
used to parse your ontology XML file via the SAX API.  The parsed output
can be used to produce a visualization of your ontology, such as with D3.js.

### The FastAPI entry-point modules

The entry-point for the two microservices are:

- impl1/app_web/webapp.py
- impl1/app_graph/websvc.py

These two are very similar in that they create the **FastAPI** object,
load environment variables, configure logging, log the environment variables,
and define the HTTP endpoints.

The following is an example from the AI microservice.

```
# standard initialization
load_dotenv(override=True)
logging.basicConfig(
    format="%(asctime)s - %(message)s", level=LoggingLevelService.get_level()
)
ConfigService.log_defined_env_vars()

app = FastAPI()
ai_svc = AiService()
```

#### /liveness endpoints

Each microservice implements a **/liveness** HTTP GET endpoint that
can be executed by the container orchestration system (i.e - ACA or AKS)
to ensure the process is alive, and restart it if not.


#### Authorization and Authentication 

Since each customer organization is expected to have their own specific
security requirements, Authorization and Authentication is **not**
implemented in this reference application.

[msal](https://learn.microsoft.com/en-us/entra/msal/python/) is one
library you may wish to use to implement authorization and authencication
with [Microsoft Entra (AAD)](https://www.microsoft.com/en-us/security/business/identity-access/microsoft-entra-id).

On a networking level, however, the **Azure Container App** will user
use its' own, or an injected, Virtual network.  So the back-end microservices
can be defined as "internal" and not receive external network requests.

Additionally, **middleware** can be used in the Graph Microservice
such that a known HTTP header must be populated with a known value before
the HTTP request is accepted and processed.  Otherwise, a HTTP 401
return code is returned.  See "@app.middleware("http")" in file
**app_graph\websvc.py**.

---

## Code formatting with the black library

The [black](https://pypi.org/project/black/) library is used to reformat
all python source code (i.e - the *.py files) into a standard and **pythonic**
style.  This can eliminate friction in Development teams by eliminating
personal coding style preferences.  In addition to reformatting the source
code, black can also identify some problems/errors in the code.

See the **code-reformat.ps1** and **code-reformat.sh** scripts in the impl directory.

It's best to run this **code-reformat.ps1** script just prior to copying
the code to the other subprojects with the **deploy_master_code.xml** Ant
script described above.

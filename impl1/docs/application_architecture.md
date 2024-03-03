# CosmosAIGraph : Application Architecture

<p align="center">
  <img src="img/app-architecture.png" width="90%">
</p>

---

## Application Components

- Microservices
  - web microervice - UI front end
  - graph microservice - Contains the in-memory rdflib graph
  - ai microservice - Implements the Azure OpenAI and LangChain logic
- Azure Container App - Runtime orchestrator for the above three microservices
- Cosmos DB Mongo vCore - Domain data and conversational AI documents
- Azure OpenAI - completions and embeddings service


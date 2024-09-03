// Bicep bicepparam entries generated by main.py on Sun Aug 25 09:21:52 2024
// Include these in your caig.bicepparam file

using './caig.bicep'

param acaEnvironmentName = readEnvironmentVariable('CAIG_ACA_ENVIRONMENT_NAME')
param azureMongoVcoreConnStr = readEnvironmentVariable('CAIG_AZURE_MONGO_VCORE_CONN_STR')
param azureOpenaiCompletionsDep = readEnvironmentVariable('CAIG_AZURE_OPENAI_COMPLETIONS_DEP')
param azureOpenaiEmbeddingsDep = readEnvironmentVariable('CAIG_AZURE_OPENAI_EMBEDDINGS_DEP')
param azureOpenaiKey = readEnvironmentVariable('CAIG_AZURE_OPENAI_KEY')
param azureOpenaiUrl = readEnvironmentVariable('CAIG_AZURE_OPENAI_URL')
param azureRegion = readEnvironmentVariable('CAIG_AZURE_REGION')
param configContainer = readEnvironmentVariable('CAIG_CONFIG_CONTAINER')
param conversationsContainer = readEnvironmentVariable('CAIG_CONVERSATIONS_CONTAINER')
param cosmosdbNosqlKey1 = readEnvironmentVariable('CAIG_COSMOSDB_NOSQL_KEY1')
param cosmosdbNosqlKey2 = readEnvironmentVariable('CAIG_COSMOSDB_NOSQL_KEY2')
param cosmosdbNosqlUri = readEnvironmentVariable('CAIG_COSMOSDB_NOSQL_URI')
param definedAuthUsers = readEnvironmentVariable('CAIG_DEFINED_AUTH_USERS')
param feedbackContainer = readEnvironmentVariable('CAIG_FEEDBACK_CONTAINER')
param graphNamespace = readEnvironmentVariable('CAIG_GRAPH_NAMESPACE')
param graphServiceName = readEnvironmentVariable('CAIG_GRAPH_SERVICE_NAME')
param graphSourceContainer = readEnvironmentVariable('CAIG_GRAPH_SOURCE_CONTAINER')
param graphSourceDb = readEnvironmentVariable('CAIG_GRAPH_SOURCE_DB')
param graphSourceOwlFilename = readEnvironmentVariable('CAIG_GRAPH_SOURCE_OWL_FILENAME')
param graphSourceRdfFilename = readEnvironmentVariable('CAIG_GRAPH_SOURCE_RDF_FILENAME')
param graphSourceType = readEnvironmentVariable('CAIG_GRAPH_SOURCE_TYPE')
param laWorkspaceName = readEnvironmentVariable('CAIG_LA_WORKSPACE_NAME')
param pgFlexPass = readEnvironmentVariable('CAIG_PG_FLEX_PASS')
param pgFlexServer = readEnvironmentVariable('CAIG_PG_FLEX_SERVER')
param pgFlexUser = readEnvironmentVariable('CAIG_PG_FLEX_USER')
param websvcAuthHeader = readEnvironmentVariable('CAIG_WEBSVC_AUTH_HEADER')
param websvcAuthValue = readEnvironmentVariable('CAIG_WEBSVC_AUTH_VALUE')
param webAppName = readEnvironmentVariable('CAIG_WEB_APP_NAME')


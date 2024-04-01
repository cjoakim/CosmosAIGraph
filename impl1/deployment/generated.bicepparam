// Bicep bicepparam entries generated by main.py on Mon Apr  1 16:22:20 2024
// Include these in your caig.bicepparam file

using './caig.bicep'

param acaEnvironmentName = readEnvironmentVariable('CAIG_ACA_ENVIRONMENT_NAME')
param azureMongoVcoreConnStr = readEnvironmentVariable('CAIG_AZURE_MONGO_VCORE_CONN_STR')
param azureOpenaiCompletionsDep = readEnvironmentVariable('CAIG_AZURE_OPENAI_COMPLETIONS_DEP')
param azureOpenaiEmbeddingsDep = readEnvironmentVariable('CAIG_AZURE_OPENAI_EMBEDDINGS_DEP')
param azureOpenaiKey = readEnvironmentVariable('CAIG_AZURE_OPENAI_KEY')
param azureOpenaiUrl = readEnvironmentVariable('CAIG_AZURE_OPENAI_URL')
param azureRegion = readEnvironmentVariable('CAIG_AZURE_REGION')
param conversationsContainer = readEnvironmentVariable('CAIG_CONVERSATIONS_CONTAINER')
param definedAuthUsers = readEnvironmentVariable('CAIG_DEFINED_AUTH_USERS')
param documentsContainer = readEnvironmentVariable('CAIG_DOCUMENTS_CONTAINER')
param graphServiceName = readEnvironmentVariable('CAIG_GRAPH_SERVICE_NAME')
param graphSourceContainer = readEnvironmentVariable('CAIG_GRAPH_SOURCE_CONTAINER')
param graphSourceDb = readEnvironmentVariable('CAIG_GRAPH_SOURCE_DB')
param graphSourceOwlFilename = readEnvironmentVariable('CAIG_GRAPH_SOURCE_OWL_FILENAME')
param graphSourceRdfFilename = readEnvironmentVariable('CAIG_GRAPH_SOURCE_RDF_FILENAME')
param graphSourceType = readEnvironmentVariable('CAIG_GRAPH_SOURCE_TYPE')
param laWorkspaceName = readEnvironmentVariable('CAIG_LA_WORKSPACE_NAME')
param logLevel = readEnvironmentVariable('CAIG_LOG_LEVEL')
param webAppName = readEnvironmentVariable('CAIG_WEB_APP_NAME')


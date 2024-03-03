
// This is the Bicep deployment script for the CosmosAIGraph
// Azure Container Apps (ACA) part of the solution.
// It will deploy the web application and supporting web services
// from public container images on DockerHub.
// Cosmos DB and OpenAI deployment is NOT handled by this script; only ACA.
// Chris Joakim, Microsoft

param acaEnvironmentName string
param aiServiceName string
param azureMongoVcoreConnStr string
param azureOpenaiCompletionsDep string
param azureOpenaiEmbeddingsDep string
param azureOpenaiKey string
param azureOpenaiUrl string
param azureRegion string
param definedAuthUsers string
param graphServiceName string
param graphSourceContainer string
param graphSourceDb string
param graphSourceOwlFilename string
param graphSourceRdfFilename string
param graphSourceType string
param laWorkspaceName string
param logLevel string
param webAppName string

resource law 'Microsoft.OperationalInsights/workspaces@2020-03-01-preview' = {
  name: laWorkspaceName
  location: azureRegion
  properties: any({
    retentionInDays: 30
  })
}

resource acaEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: acaEnvironmentName
  location: azureRegion 
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: law.listKeys().primarySharedKey
      }
    }
    peerAuthentication: {
      mtls: {
        enabled: false
      }
    }
    zoneRedundant: false
  }
}

resource graph 'Microsoft.App/containerApps@2023-05-01' = {
  name: graphServiceName
  location: azureRegion
  properties: {
    environmentId: acaEnvironment.id
    configuration: {
      ingress: {
        allowInsecure: true
        clientCertificateMode: 'ignore'
        targetPort: 8001
        external: true
        stickySessions: {
          affinity: 'none'
        }
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          image: 'cjoakim/caig_graph:latest'
          name: graphServiceName
          env: [
            {
              name: 'CAIG_GRAPH_SOURCE_TYPE'
              value: graphSourceType
            }
            {
              name: 'CAIG_GRAPH_SOURCE_OWL_FILENAME'
              value: graphSourceOwlFilename
            }
            {
              name: 'CAIG_GRAPH_SOURCE_RDF_FILENAME'
              value: graphSourceRdfFilename
            }
            {
              name: 'CAIG_AZURE_MONGO_VCORE_CONN_STR'
              value: azureMongoVcoreConnStr
            }
            {
              name: 'CAIG_GRAPH_SOURCE_DB'
              value: graphSourceDb
            }
            {
              name: 'CAIG_GRAPH_SOURCE_CONTAINER'
              value: graphSourceContainer
            }
          ]
          probes: [
            {
              type: 'liveness'
              failureThreshold: 5
              httpGet: {
                path: '/liveness'
                port:  8001
                scheme: 'http'
              }
              initialDelaySeconds: 60
              periodSeconds: 120
              successThreshold: 1
              timeoutSeconds: 10
            }
          ]
        }
      ]
      scale: {
        maxReplicas: 2
        minReplicas: 1
      }
      terminationGracePeriodSeconds: 30
    }
  }
}

resource ai 'Microsoft.App/containerApps@2023-05-01' = {
  name: aiServiceName
  location: azureRegion
  properties: {
    environmentId: acaEnvironment.id
    configuration: {
      ingress: {
        allowInsecure: true
        clientCertificateMode: 'ignore'
        targetPort: 8002
        external: true
        stickySessions: {
          affinity: 'none'
        }
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          image: 'cjoakim/caig_ai:latest'
          name: graphServiceName
          env: [
            {
              name: 'CAIG_AZURE_OPENAI_URL'
              value: azureOpenaiUrl
            }
            {
              name: 'CAIG_AZURE_OPENAI_KEY'
              value: azureOpenaiKey
            }
            {
              name: 'CAIG_AZURE_OPENAI_VERSION'
              value: '2023-12-01-preview'
            }
            {
              name: 'CAIG_AZURE_OPENAI_REGION'
              value: azureOpenaiRegion
            }
            {
              name: 'CAIG_AZURE_OPENAI_COMPLETIONS_DEP'
              value: azureOpenaiCompletionsDep
            }
            {
              name: 'CAIG_AZURE_OPENAI_EMBEDDINGS_DEP'
              value: azureOpenaiEmbeddingsDep
            }
            {
              name: 'CAIG_GRAPH_SOURCE_OWL_FILENAME'
              value: graphSourceOwlFilename
            }
            {
              name: 'CAIG_LOG_LEVEL'
              value: logLevel
            }
          ]
          probes: [
            {
              type: 'liveness'
              failureThreshold: 5
              httpGet: {
                path: '/liveness'
                port:  8002
                scheme: 'http'
              }
              initialDelaySeconds: 60
              periodSeconds: 120
              successThreshold: 1
              timeoutSeconds: 10
            }
          ]
        }
      ]
      scale: {
        maxReplicas: 2
        minReplicas: 1
      }
      terminationGracePeriodSeconds: 30
    }
  }
}

resource web 'Microsoft.App/containerApps@2023-05-01' = {
  name: webAppName
  location: azureRegion
  properties: {
    environmentId: acaEnvironment.id
    configuration: {
      ingress: {
        allowInsecure: true
        clientCertificateMode: 'ignore'
        targetPort: 8000
        external: true
        stickySessions: {
          affinity: 'none'
        }
        transport: 'http'
      }
    }
    template: {
      containers: [
        {
          image: 'cjoakim/caig_web:latest'
          name: webAppName
          env: [
            {
              name: 'CAIG_GRAPH_SERVICE_URL'
              value: 'http://${graph.properties.latestRevisionFqdn}'
            }
            {
              name: 'CAIG_GRAPH_SERVICE_PORT'
              value: '80'
            }
            {
              name: 'CAIG_AI_SERVICE_URL'
              value: 'http://${ai.properties.latestRevisionFqdn}'
            }
            {
              name: 'CAIG_AI_SERVICE_PORT'
              value: '80'
            }
            {
              name: 'CAIG_DEFINED_AUTH_USERS'
              value: definedAuthUsers
            }
            {
              name: 'CAIG_LOG_LEVEL'
              value: '5'
            }
            {
              name: 'CAIG_AZURE_MONGO_VCORE_CONN_STR'
              value: azureMongoVcoreConnStr
            }
          ]
          probes: [
            {
              type: 'liveness'
              failureThreshold: 5
              httpGet: {
                path: '/liveness'
                port:  8000
                scheme: 'http'
              }
              initialDelaySeconds: 60
              periodSeconds: 120
              successThreshold: 1
              timeoutSeconds: 10
            }
          ]
        }
      ]
      scale: {
        maxReplicas: 2
        minReplicas: 1
      }
      terminationGracePeriodSeconds: 10
    }
  }
}

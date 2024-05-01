# CosmosAIGraph - Impl2 IMDb Graph Deployment

Azure Container App deployment process.

This page assumes that you have executed the data downloading,
wrangling, and Cosmos DB Mongo vCore document loading process
described in the readme.md file in the impl2\ directory.

## Links

- https://learn.microsoft.com/en-us/cli/azure/
- https://learn.microsoft.com/en-us/azure/container-apps/tutorial-deploy-first-app-cli
- https://learn.microsoft.com/en-us/azure/container-apps/workload-profiles-manage-cli?tabs=external-env&pivots=aca-vnet-managed#add-profiles

## Deployment with the az CLI

### Install the az CLI

See the following links for Windows, Mac OS, and Linux:

- https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows?tabs=azure-cli
- https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-macos
- https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-linux?pivots=apt

### Initial az CLI setup

```
> az --version

> az upgrade

> az login

> az account set --subscription $Env:AZURE_SUBSCRIPTION_ID

> az extension add --name containerapp --upgrade

> az extension list

> az provider register --namespace Microsoft.App

> az provider register --namespace Microsoft.OperationalInsights
```

### See the available workload profiles for Azure Container Apps

These can be used for large-memory graph deployments.
The deployment script in this directory uses an **E4** profile.
Choose a profile appropriate for the size of your graph.

```
> .\az_workload_profiles.ps1

Name         Cores    MemoryGiB    Category
-----------  -------  -----------  ---------------
D4           4        16           GeneralPurpose
D8           8        32           GeneralPurpose
D16          16       64           GeneralPurpose
D32          32       128          GeneralPurpose
E4           4        32           MemoryOptimized
E8           8        64           MemoryOptimized
E16          16       128          MemoryOptimized
E32          32       256          MemoryOptimized
Consumption  4        8            Consumption
```

### Execute the deployment script

```
> .\az_imdb_deploy.ps1 
```

Note 1: Edit your environment variables used by **az_imdb_deploy.ps1**,
and also the configuration parameters at the top of the script

Note 2: The line in **az_imdb_deploy.ps1** which contains the line **--env-vars**
can be generated for you by running command **python main.py build_az_cli_env_vars**
in the impl2\ directory.  Replace the value of CAIG_AZURE_MONGO_VCORE_CONN_STR
in this generated one-line script with a dummy value like 'xxx'.
Then, post-deployment, in Azure Portal set the value of CAIG_AZURE_MONGO_VCORE_CONN_STR
to the actual connection string.

Note 3: When deployment is complete, go to the ACA container in Azure Portal
and see the URL of the container.  Open this URL with your web browser.
Also see the log stream for the container in Azure portal for any configuration
errors, as well as to observe the loading of the graph from vCore.

Note 4: The in-memory rdflib graph in the ACA container is loaded from
the data in the imdb container in Cosmos DB Mongo vCore.

TODO - Enhance this deployment process so that the special characters in
the CAIG_AZURE_MONGO_VCORE_CONN_STR connection string are handled properly
by az CLI.

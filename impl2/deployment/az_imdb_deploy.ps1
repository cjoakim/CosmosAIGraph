

# references:
# https://learn.microsoft.com/en-us/azure/container-apps/workload-profiles-manage-cli?tabs=external-env&pivots=aca-vnet-managed#add-profiles
# https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/container-apps/add-ons-qdrant.md

# script boolean flags
$DISPLAY_VALUES = 1
$CREATE_RESOURCE_GROUP = 1
$CREATE_CONTAINER_APP_ENV = 1
$CREATE_WORKLOAD_PROFILE = 1
$CREATE_CONTAINER_APP = 1

# configuration parameters
$RESOURCE_GROUP = "caigimdbaca12"
$LOCATION ="eastus"
$APP_ENVIRONMENT = "caigimdb"
$APP_NAME = "caigimdb"
$WORKLOAD_PROFILE_TYPE="E4"
$WORKLOAD_PROFILE_NAME="E4"
$CPU_SIZE = "4.0"
$MEMORY_SIZE = "16.0Gi"
$DOCKER_IMAGE = "cjoakim/caig_impl2_web:latest"

if ($DISPLAY_VALUES -eq 1) {
    Write-Host  "========================================"
    Write-Host  "displaying configuration values ..."
    Write-Host  "REGION:                $($LOCATION)" 
    Write-Host  "RESOURCE_GROUP:        $($RESOURCE_GROUP)" 
    Write-Host  "APP_ENVIRONMENT:       $($APP_ENVIRONMENT)" 
    Write-Host  "WORKLOAD_PROFILE_TYPE: $($WORKLOAD_PROFILE_TYPE)"
    Write-Host  "WORKLOAD_PROFILE_NAME: $($WORKLOAD_PROFILE_NAME)"
    Write-Host  "CPU_SIZE:              $($CPU_SIZE)"
    Write-Host  "MEMORY_SIZE:           $($MEMORY_SIZE)" 
    Write-Host  "DOCKER_IMAGE:          $($DOCKER_IMAGE)" 
    Write-Host  "---"
    Write-Host  "displaying supported workload profiles ..."
    az containerapp env workload-profile list-supported `
        --location $LOCATION `
        --query "[].{Name: name, Cores: properties.cores, MemoryGiB: properties.memoryGiB, Category: properties.category}" `
        -o table
    # Name         Cores    MemoryGiB    Category
    # -----------  -------  -----------  ---------------
    # D4           4        16           GeneralPurpose
    # D8           8        32           GeneralPurpose
    # D16          16       64           GeneralPurpose
    # D32          32       128          GeneralPurpose
    # E4           4        32           MemoryOptimized
    # E8           8        64           MemoryOptimized
    # E16          16       128          MemoryOptimized
    # E32          32       256          MemoryOptimized
    # Consumption  4        8            Consumption
}

if ($CREATE_RESOURCE_GROUP -eq 1) {
    Write-Host  "========================================"
    Write-Host  "creating resource group ..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
}

if ($CREATE_CONTAINER_APP_ENV -eq 1) {
    Write-Host  "========================================"
    Write-Host  "creating container app env ..."
    az containerapp env create `
        --name $APP_ENVIRONMENT `
        --resource-group $RESOURCE_GROUP `
        --location $LOCATION `
        --enable-workload-profiles
}

if ($CREATE_WORKLOAD_PROFILE -eq 1) {
    Write-Host  "========================================"
    Write-Host  "creating workload-profile ..."
    az containerapp env workload-profile add `
        --name $APP_ENVIRONMENT `
        --resource-group $RESOURCE_GROUP `
        --workload-profile-type $WORKLOAD_PROFILE_TYPE `
        --workload-profile-name $WORKLOAD_PROFILE_NAME `
        --min-nodes 0 `
        --max-nodes 2
}

if ($CREATE_CONTAINER_APP -eq 1) {
    Write-Host  "========================================"
    Write-Host  "creating container app ..."
    az containerapp create `
        --name           $APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --environment    $APP_ENVIRONMENT `
        --workload-profile-name $WORKLOAD_PROFILE_NAME `
        --cpu    $CPU_SIZE `
        --memory $MEMORY_SIZE `
        --image  $DOCKER_IMAGE `
        --min-replicas 1 `
        --max-replicas 1 `
        --ingress external `
        --target-port 8000 `
        --transport auto `
        --env-vars '<replace this line with the output of python main.py build_az_cli_env_vars>' `
        --query properties.outputs.fqdn `
}
Write-Host  "done"


# NOTE: In impl2 directory, run command 'python main.py build_az_cli_env_vars'
# then replace the --env-vars line, above, with the output of the command.
# Then, when the container is started, update the values of environment variables
# that have 'xxx' as a value; namely CAIG_AZURE_MONGO_VCORE_CONN_STR.
# This creates another revision of the container, such as v2.

# --env-vars is A list of environment variable(s) for the container.
# Space-separated values in 'key=value' format.

# TODO: enhance this az CLI deployment to use ALL environment variables
# even if they contain special characters like the CAIG_AZURE_MONGO_VCORE_CONN_STR.

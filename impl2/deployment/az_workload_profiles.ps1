

$REGION="eastus"

# https://learn.microsoft.com/en-us/azure/container-apps/workload-profiles-manage-cli?tabs=external-env&pivots=aca-vnet-managed#add-profiles

az containerapp env workload-profile list-supported `
    --location $REGION `
    --query "[].{Name: name, Cores: properties.cores, MemoryGiB: properties.memoryGiB, Category: properties.category}" `
    -o table

# PS ...\deployment> .\az_workload_profiles.ps1
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


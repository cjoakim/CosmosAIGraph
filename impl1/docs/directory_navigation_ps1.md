# CosmosAIGraph : Directory Navigation Script

Since this reference application is implemented as several microservices
it can be challenging for some users to navigate between these
directories with multiple **cd** commands.

Therefore, we've created this **Navigation Function** that you can add
to your **Windows 11 Profile** file.  When you execute the **caig** function
you'll see a menu like the following.  Simply enter the directory number you wish
to navigate to.

<p align="center">
  <img src="img/powershell-nav-function.png" width="50%">
</p>

This function requires that you've set your **CAIG_HOME** environment variable
which is the root directory on your system where this GitHub repo resides.

### Add this function to your Windows 11 Profile

```
function caig {
    cls
    Write-Host "CosmosAIGraph Directory Navigation"
    Write-Host "0) repo root"
    Write-Host "1) impl1"
    Write-Host "2) impl1\app_ai"
    Write-Host "3) impl1\app_common"
    Write-Host "4) impl1\app_console"
    Write-Host "5) impl1\app_graph"
    Write-Host "6) impl1\app_web"
    Write-Host "7) impl1\data"
    Write-Host "8) impl1\deployment"
    $input = Read-Host "Enter directory number "
    switch ($input) {
      '0' {
          cd $Env:CAIG_HOME
          return
      }
      '1' {
          cd $Env:CAIG_HOME\impl1
          return
      }
      '2' {
          cd $Env:CAIG_HOME\impl1\app_ai
          return
      }
      '3' {
          cd $Env:CAIG_HOME\impl1\app_common
          return
      }
      '4' {
          cd $Env:CAIG_HOME\impl1\app_console
          return
      }
      '5' {
          cd $Env:CAIG_HOME\impl1\app_graph
          return
      }
      '6' {
          cd $Env:CAIG_HOME\impl1\app_web
          return
      }
      '7' {
          cd $Env:CAIG_HOME\impl1\data
          return
      }
      '8' {
          cd $Env:CAIG_HOME\impl1\deployment
          return
      }
    }
}
```


In WindowsPowershell you can execute the following command to
get the filesystem location of your Windows profile:

```
> $profile
```
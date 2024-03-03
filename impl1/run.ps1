Set-Location .\app_graph
$ArgList = ".\run.ps1"
Start-Process -FilePath PowerShell -ArgumentList $ArgList -NoNewWindow
Set-Location ..\app_web
Start-Process -FilePath PowerShell -ArgumentList $ArgList
Set-Location ..\app_ai
Start-Process -FilePath PowerShell -ArgumentList $ArgList
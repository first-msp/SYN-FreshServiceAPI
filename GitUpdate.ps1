Stop-Service -Name W3SVC
Stop-ScheduledTask -TaskName "RunCeleryWorker"
Stop-Process -Name celery
Set-Location -Path C:\inetpub\wwwroot\
Remove-Item -Recurse -Force .\SYN-FreshServiceAPI
git clone https://github.com/ashleycollinge1/SYN-FreshServiceAPI
Start-Service -Name W3SVC
Start-ScheduledTask -TaskName "RunCeleryWorker"
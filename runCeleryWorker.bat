cd C:\inetpub\wwwroot\SYN-FreshServiceAPI\app
celery -A  __init__ worker --loglevel=info --logfile=C:\inetpub\logs\SYN-FreshServiceAPI\celery.log --quiet
server {
       listen 443 ssl;
       server_name phantom-load.in;

       ssl_certificate /etc/ssl/certs/phantom-load.in-certificate.crt;
       ssl_certificate_key /etc/ssl/private/phantom-load.in-PrivateKey.pem;
       ssl_trusted_certificate /etc/ssl/certs/phantom-load.in-intermediate.pem;

       proxy_set_header        Access-Control-Allow-Origin: https://www.phantom-load.in;


       location = /favicon.ico {access_log off;log_not_found off;}

        location /static/ {
            alias /home/hpbhvac/Django/phantomload/staticfiles/;
        }

        location /media/ {
            alias /home/hpbhvac/Django/phantomload/media/;
        }

        location / {
            include proxy_params;
            proxy_pass http://unix:/home/hpbhvac/Django/phantomload/gameauth.sock;
        }
     }

server {
    listen 80;
    server_name phantom-load.in;

    # Redirect all HTTP traffic to HTTPS
    if ($host = phantom-load.in) {
        return 301 https://$host$request_uri;
    }

    return 404;  # Default response for non-HTTPS requests
}

#!/usr/bin/bash

## one step
#openssl req -new -x509 -keyout test.pem -out test.pem -days 365 -nodes


## or...

openssl genrsa -out key.pem 1024
openssl req -new -key key.pem -out request.pem
openssl x509 -req -days 30 -in request.pem -signkey key.pem -out certificate.pem

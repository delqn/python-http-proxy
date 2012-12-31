#!/usr/bin/bash

openssl req -new -x509 -keyout test.pem -out test.pem -days 365 -nodes

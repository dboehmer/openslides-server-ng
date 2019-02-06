# OpenSlides-Server-ng

Experimental concept code of a new server implementation for OpenSlides.

This repository contains an implementation of the server in python and one in
go. The test_client is a benchmark program, that connects many clients to the
server and sends write requests.

## install

You need python >= 3.7

    pip install -r requriements.txt


## Run Python Server

    python python/run.py


## Run Go Server

    cd go
    go build && ./openslides-server


## Run test client


    python test_client/run.py


You can use the Firefox Add-on
[Browser WebSocket Client](https://addons.mozilla.org/de/firefox/addon/browser-websocket-client/)
to test the server.

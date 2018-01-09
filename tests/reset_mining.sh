#!/bin/bash
sqlite3 etc/data/main.db "UPDATE PROXY_LIST SET LAST_MINED=0"
python src/px-daemon.py

#!/bin/bash
sqlite3 etc/data/main.db "UPDATE RENEWAL SET EPOCH = 0;"
python src/px-daemon.py

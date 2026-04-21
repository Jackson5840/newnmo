#!/bin/bash
set -e
psql -U nmo < /tmp/dumpall_back3.sql 

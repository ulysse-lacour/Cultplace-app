#!/bin/bash
echo "Creating develop db"

psql -d postgres -c "CREATE ROLE cultplace WITH LOGIN PASSWORD 'tomtom';"
psql -d postgres -c "CREATE DATABASE cultplace with OWNER cultplace;"

echo "Develop db created"

echo "Creating test db"

psql -d postgres -c "CREATE ROLE test WITH LOGIN PASSWORD 'test';"
psql -d postgres -c "CREATE DATABASE test with OWNER test;"

echo "Test db created"

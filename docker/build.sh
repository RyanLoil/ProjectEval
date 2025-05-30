#!/bin/bash
timestamp=$(date +%Y%m%d%H%M%S)
version_tag="projecteval-execution:$timestamp"
cd ..
docker build -f docker/Dockerfile -t "$version_tag" .
docker tag "$version_tag" projecteval-execution:latest

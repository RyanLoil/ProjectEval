@echo off
for /f %%i in ('powershell -Command "Get-Date -Format yyyyMMddHHmmss"') do set timestamp=%%i
set version_tag=projecteval-execution:%timestamp%
cd ..
docker build -f docker/Dockerfile -t %version_tag% .
docker tag %version_tag% projecteval-execution:latest
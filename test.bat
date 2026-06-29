@echo off
docker build -t geronlineagent . && docker run -d --rm -p 8000:8000 -v .:/app geronlineagent

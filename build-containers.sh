#!/bin/bash
podman build -f ./backend/Dockerfile.backend --target run-backend -t syosetu-epubifier-backend:latest ./backend/
podman build -f ./backend/Dockerfile.backend --target run-rqworker -t syosetu-epubifier-rqworker:latest ./backend/
podman build -f ./frontend/Dockerfile.frontend -t syosetu-epubifier-frontend:latest ./frontend/

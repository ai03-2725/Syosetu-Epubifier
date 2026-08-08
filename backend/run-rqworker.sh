#!/bin/bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
python manage.py rqworker default

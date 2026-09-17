#!/usr/bin/env bash
# Easy launcher for Trading Bot GUI
cd "$(dirname "$0")"
exec venv/bin/python gui/app.py

#!/usr/bin/env bash

source .venv/bin/activate
hypercorn libbygui.main:app --reload --bind 0.0.0.0:8060
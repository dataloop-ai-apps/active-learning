#!/bin/bash

rm -r ./dist ./panels
npm i
npm run build
python3 ./build.py
rm -r ./dist
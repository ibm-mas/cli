#!/bin/bash

if [[ "$TEST" == '8.7.x' || "$TEST" == '8.7.X' ]]; then
  echo "TEST IS 8.7.x|X"
else
  echo "TEST is NOT 8.7.x|X"
fi

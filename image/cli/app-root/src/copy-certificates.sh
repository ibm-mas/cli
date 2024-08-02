#!/bin/bash

appList=(
  "core"
  "arcgis"
  "assist" 
  "iot"
  "manage"
  "monitor"
  "optimizer"  
  "predict"
  "visualinspection"
)

if [ -e "/workspace/certificates" ]; then
  for app in ${appList[@]}; do
    # tls.crt and tls.key will always exist if pipeline is configured to use manual certificates
    if [[ -f "/workspace/certificates/$app.tls.crt" ]]; then  
      echo "Copying certs from $app into configs workspace"
      mkdir -p /workspace/configs/certs/$app
      cp /workspace/certificates/$app.tls.crt /workspace/configs/certs/$app/tls.crt
      cp /workspace/certificates/$app.tls.key /workspace/configs/certs/$app/tls.key      
      # ca.crt may be empty, but file must exist
      if [[ -f "/workspace/certificates/$app.ca.crt" ]]; then  
        cp /workspace/certificates/$app.ca.crt /workspace/configs/certs/$app/ca.crt
      else
        touch /workspace/configs/certs/$app/ca.crt
      fi
      echo "Done"
    fi    
  done  
fi

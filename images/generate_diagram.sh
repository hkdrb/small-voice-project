#!/bin/bash

# Determine the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to that directory
cd "$SCRIPT_DIR"

# Run mermaid-cli
npx -p @mermaid-js/mermaid-cli mmdc -i er_diagram.mmd -o er_diagram.png -b transparent -s 8

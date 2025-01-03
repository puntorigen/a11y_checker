#!/bin/sh

GITHUB_TOKEN=$1
OPENAI_API_KEY=$2
export PYTHONUNBUFFERED=1 # this is to make sure that the output is not buffered and is printed in real-time

if [ -z "$OPENAI_API_KEY" ]; then
  # export args as ENV variables
  export GITHUB_TOKEN=$GITHUB_TOKEN
  echo "OpenAI API key not provided. Starting Ollama using Shell..."
  /bin/sh -c /install_ollama.sh
else
  echo "OpenAI API key provided. Skipping Ollama installation."
fi

echo "Running the script... $@"
python -u /a11y_checker.py "$@"

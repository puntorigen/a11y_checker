#!/bin/sh
echo "OpenAI API key not provided. Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh
sleep 10
echo "Starting Ollama server in background thread..."
ollama serve > /dev/null 2>&1 &
sleep 10
echo "Downloading Ollama model... 4.1 GB"
ollama pull "phi3:3.8b-mini-instruct-q8_0" > /dev/null 2>&1
sleep 10
#!/usr/bin/env bash
set -e

echo "Устанавливаю Ollama..."
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.ai/install.sh | sh
else
  echo "Ollama уже установлена"
fi

echo "Скачиваю модели..."
ollama pull llama3.2:3b-instruct-q4_K_M
ollama pull mistral:7b-instruct-q4_K_M
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull gemma2:2b-instruct-q4_K_S

echo "Готово."

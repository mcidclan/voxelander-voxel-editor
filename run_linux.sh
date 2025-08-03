#!/bin/bash

ENV_DIR="env"
REQUIRED_PACKAGES=("PyOpenGL" "glfw" "numpy" "imgui")
MAIN_SCRIPT="main.py"

function packagesInstalled() {
  source "$ENV_DIR/bin/activate"
  for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! pip show "$pkg" > /dev/null 2>&1; then
      deactivate
      return 1
    fi
  done
  deactivate
  return 0
}

function installPackages() {
  echo "Installing required packages..."
  source "$ENV_DIR/bin/activate"
  pip install --upgrade pip setuptools
  pip install "${REQUIRED_PACKAGES[@]}"
  deactivate
}

function envExists() {
  [ -d "$ENV_DIR" ]
}

function createEnv() {
  echo "Create virtual env..."
  python3 -m venv "$ENV_DIR" || { echo "Error during env setup."; exit 1; }
}

function activateAndRun() {
  echo "Activate env and run..."
  source "$ENV_DIR/bin/activate"
  python "$MAIN_SCRIPT"
  deactivate
}

if envExists; then
  echo "Env found."
  if packagesInstalled; then
    echo "Packages available."
  else
    echo "Packages missing, installing..."
    installPackages
  fi
else
  echo "Env not found, creation please wait.."
  createEnv
  installPackages
fi

activateAndRun


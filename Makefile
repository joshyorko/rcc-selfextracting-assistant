# Makefile for RCC Self-Extracting Assistant Builder
# 
# Usage:
#   make build          - Build the self-extracting assistant
#   make test           - Build and test the assistant
#   make clean          - Remove build artifacts
#   make help           - Show this help message

# Configuration - customize these for your environment
RCC ?= rcc.exe
RCC_HOME ?= $(HOME)/.robocorp/holotree
ROBOT ?= fetch-repos-bot
OUTPUT ?= assistant.py

# Python interpreter
PYTHON ?= python3

.PHONY: help build test clean validate

help:
	@echo "RCC Self-Extracting Assistant Builder"
	@echo ""
	@echo "Available targets:"
	@echo "  make build          - Build the self-extracting assistant"
	@echo "  make test           - Build and test the assistant"
	@echo "  make clean          - Remove build artifacts"
	@echo "  make validate       - Validate required files exist"
	@echo ""
	@echo "Configuration (set via environment or make arguments):"
	@echo "  RCC=$(RCC)"
	@echo "  RCC_HOME=$(RCC_HOME)"
	@echo "  ROBOT=$(ROBOT)"
	@echo "  OUTPUT=$(OUTPUT)"
	@echo ""
	@echo "Example:"
	@echo "  make build RCC=/path/to/rcc.exe ROBOT=my-robot"

validate:
	@echo "Validating required files..."
	@test -f "launcher.py" || (echo "ERROR: launcher.py not found" && exit 1)
	@test -f "builder.py" || (echo "ERROR: builder.py not found" && exit 1)
	@echo "✓ Core files present"

build: validate
	@echo "Building self-extracting assistant..."
	$(PYTHON) builder.py \
		--rcc "$(RCC)" \
		$(if $(wildcard $(RCC_HOME)),--rcc-home "$(RCC_HOME)",) \
		--robot "$(ROBOT)" \
		--output "$(OUTPUT)"
	@echo ""
	@echo "✓ Build complete: $(OUTPUT)"
	@ls -lh "$(OUTPUT)"

test: build
	@echo ""
	@echo "Testing self-extracting assistant..."
	@echo "Note: This will extract the payload and attempt to run RCC"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read dummy
	$(PYTHON) "$(OUTPUT)"

clean:
	@echo "Cleaning build artifacts..."
	rm -f "$(OUTPUT)"
	rm -f payload.zip
	rm -f *.tmp
	@echo "✓ Clean complete"

# Advanced targets

# Build with custom launcher
build-custom: validate
	@test -n "$(CUSTOM_LAUNCHER)" || (echo "ERROR: Set CUSTOM_LAUNCHER=/path/to/launcher.py" && exit 1)
	$(PYTHON) builder.py \
		--rcc "$(RCC)" \
		$(if $(wildcard $(RCC_HOME)),--rcc-home "$(RCC_HOME)",) \
		--robot "$(ROBOT)" \
		--launcher "$(CUSTOM_LAUNCHER)" \
		--output "$(OUTPUT)"

# Download and build with fetch-repos-bot
build-example:
	@echo "Building example with fetch-repos-bot..."
	@if [ ! -d "fetch-repos-bot" ]; then \
		echo "Cloning fetch-repos-bot..."; \
		git clone https://github.com/joshyorko/fetch-repos-bot.git; \
	fi
	$(MAKE) build ROBOT=fetch-repos-bot

.DEFAULT_GOAL := help

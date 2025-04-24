# ds-indexer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![DipDup 8.x](https://img.shields.io/badge/DipDup-8.x-green.svg)](https://dipdup.io/)

A blockchain indexer built with DipDup for defi.space protocol, providing real-time data indexing and querying capabilities for Starknet.

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Quick Installation](#quick-installation)
  - [Manual Installation](#manual-installation)
- [Usage](#usage)
  - [Running the Indexer](#running-the-indexer)
  - [Configuration Options](#configuration-options)
  - [Development Commands](#development-commands)
- [Architecture](#architecture)
  - [Core Components](#core-components)
  - [Project Structure](#project-structure)
- [Performance Considerations](#performance-considerations)
- [Contributing](#contributing)
- [License](#license)

## 🔍 Overview

This indexer leverages DipDup, a powerful indexing framework to efficiently process and index StarkNet blockchain data, making it readily available for applications and analytics.

The indexer tracks key protocol components including AMM (Automated Market Maker) operations, Yield Farming activities, Gaming Sessions, and Faucet operations, providing comprehensive data for DeFi applications.

## ✨ Features

- **Real-time Indexing**: Process blockchain data as it's produced
- **Comprehensive Data Models**: Track AMM, Yield Farming, Gaming, and Faucet activities
- **Flexible Storage Options**: Support for SQLite (development) and PostgreSQL (production)
- **Scalable Architecture**: Designed to handle growing data volumes
- **Rich Query Capabilities**: Access detailed protocol metrics and user positions
- **Production-Ready**: Docker Compose setup for production deployments
- **Hasura Integration**: GraphQL API with rich query capabilities
- **Periodic Jobs**: Automated data aggregation and metrics calculation

## 🚀 Installation

### Prerequisites

- Linux/macOS system (Windows users should use WSL)
- Python 3.12
- Basic Python environment (`python3.12 -m ensurepip`)

### Quick Installation

The easiest way to get started is using our install script:

```bash
# Make the script executable
chmod +x install.sh

# Run the install script
bash install.sh
```

This script will:
1. Install Python 3.12 if not present
2. Install pipx for managing Python applications
3. Install DipDup CLI and PDM package manager
4. Initialize the PDM project and create a virtual environment
5. Install project dependencies
6. Create initial .env file from template

### Manual Installation

Alternatively, you can install components manually:

1. Install DipDup using the official installer:
```bash
curl -Lsf https://dipdup.io/install.py | python3.12
```

2. Set up the development environment:
```bash
# Install PDM if not already installed
pipx install pdm

# Initialize project and create virtual environment
pdm init --python 3.12 --lib
pdm venv create

# Install dependencies
pdm add "dipdup>=8,<9" --venv

# Activate virtual environment
eval "$(pdm venv activate)"
```

## 📊 Usage

### Running the Indexer

You can run the indexer in several ways:

#### In-Memory SQLite (Development)
```bash
dipdup run
```

#### Persistent SQLite
```bash
# Set custom SQLite path (optional)
export SQLITE_PATH=/path/to/db.sqlite

# Run with SQLite config
dipdup -c . -c configs/dipdup.sqlite.yaml run
```

#### Docker Compose Stack (Production)
```bash
# Navigate to deploy directory
cd defi_space_indexer/deploy

# Copy and configure environment variables
cp ../.env.example ../.env
# Edit .env file as needed

# Start the stack (PostgreSQL + Hasura)
docker-compose -f compose.yaml up
```

### Configuration Options

The indexer can be configured through:
- Environment variables
- YAML configuration files
- Command-line arguments

Key configuration files:
- `defi_space_indexer/dipdup.yaml`: Main configuration file
- `defi_space_indexer/configs/dipdup.sqlite.yaml`: SQLite-specific configuration
- `defi_space_indexer/configs/dipdup.compose.yaml`: Docker Compose configuration
- `defi_space_indexer/configs/dipdup.swarm.yaml`: Docker Swarm configuration
- `defi_space_indexer/configs/replay.yaml`: Replay configuration
- `defi_space_indexer/.env.example`: Template for environment variables

### Development Commands

The project includes a Makefile with useful commands for development:

```bash
# Install dependencies
make install

# Update dependencies
make update

# Format code
make format

# Lint code
make lint

# Build Docker image
make image

# Start Docker Compose stack
make up

# Stop Docker Compose stack
make down

# Prune Docker resources
make prune
```

## 🏗️ Architecture

### Core Components

The indexer tracks four main protocol components:

#### AMM (Automated Market Maker)
- AmmFactory contract that creates and manages trading pairs
- Trading pairs for token swaps
- Liquidity positions and events
- Swap events and pricing data

#### Yield Farming
- FarmFactory contract for managing farming pools
- Farm contracts for individual farming pools
- User stakes and rewards
- Staking and reward events

#### Game Sessions
- GameFactory contract for creating game sessions
- Game sessions for gamified staking
- Staking windows and user stakes
- Agent creation and management

#### Faucet
- FaucetFactory contract for creating token faucets
- Token claiming functionality
- Whitelist management for claimable tokens
- Claim tracking and interval management

### Project Structure

The `defi_space_indexer` package is organized as follows:

```
defi_space_indexer/
├── abi/                  # Contract ABI definitions
├── configs/              # Configuration variants
│   ├── dipdup.sqlite.yaml
│   ├── dipdup.compose.yaml
│   ├── dipdup.swarm.yaml
│   └── replay.yaml
├── deploy/               # Deployment configurations
├── handlers/             # Event handlers
│   ├── on_pair_created.py
│   ├── on_swap.py
│   ├── on_mint.py
│   └── ...
├── hooks/                # Periodic jobs and callbacks
│   ├── active_staking_window.py
│   ├── calculate_game_metrics.py
│   └── ...
├── models/               # Data models
│   ├── amm_models.py
│   ├── farming_models.py
│   ├── game_models.py
│   └── faucet_models.py
├── graphql/              # GraphQL schemas and queries
├── hasura/               # Hasura configuration
├── sql/                  # SQL queries
├── types/                # Type definitions
├── dipdup.yaml           # Main configuration
├── Makefile              # Development commands
└── .env.example          # Environment variables template
```

Key components:
- **Handlers**: Process blockchain events (50+ event types)
- **Models**: Define data structures for AMM, Farming, Gaming, and Faucet
- **Hooks**: Implement periodic jobs for metrics calculation
- **Configs**: Provide different deployment configurations

## ⚡ Performance Considerations

- **Hardware Requirements**:
  - Minimum: 1 GB RAM, 1 CPU core, 20 GB storage
  - Recommended: 2 GB+ RAM, 2+ CPU cores, 50+ GB SSD storage
  - Production: 4 GB+ RAM, 4+ CPU cores, 100+ GB SSD storage

- **Optimization Tips**:
  - Use appropriate database indexes for frequent queries
  - Consider sharding for large datasets
  - Monitor memory usage during sync operations
  - Use batch processing for high-volume operations
  - For production, use PostgreSQL instead of SQLite
  - Enable connection pooling for database connections

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

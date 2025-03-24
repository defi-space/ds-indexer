# ds-indexer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![DipDup 8.x](https://img.shields.io/badge/DipDup-8.x-green.svg)](https://dipdup.io/)

A blockchain indexer built with DipDup for defi.space protocol, providing real-time data indexing and querying capabilities.

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
- [API Examples](#api-examples)
- [Performance Considerations](#performance-considerations)
- [Contributing](#contributing)
- [License](#license)

## 🔍 Overview

This indexer leverages DipDup, a powerful indexing framework to efficiently process and index blockchain data, making it readily available for applications and analytics.

The indexer tracks key protocol components including AMM (Automated Market Maker) operations and Yield Farming activities, providing comprehensive data for DeFi applications.

## ✨ Features

- **Real-time Indexing**: Process blockchain data as it's produced
- **Comprehensive Data Models**: Track AMM and Yield Farming activities
- **Flexible Storage Options**: Support for SQLite (development) and PostgreSQL (production)
- **Scalable Architecture**: Designed to handle growing data volumes
- **Rich Query Capabilities**: Access detailed protocol metrics and user positions
- **Production-Ready**: Docker Compose setup for production deployments

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
$(pdm venv activate)
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
cd deploy

# Copy and configure environment variables
cp .env.default .env
# Edit .env file as needed

# Start the stack (PostgreSQL + Hasura)
docker-compose up
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
- `defi_space_indexer/env.example`: Template for environment variables

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
```

## 🏗️ Architecture

### Core Components

The indexer tracks two main protocol components:

#### AMM (Automated Market Maker)
- Factory contract that creates and manages trading pairs
- Trading pairs for token swaps
- Liquidity positions and events
- Swap events and pricing data

#### Yield Farming
- Powerplant contract for managing farming pools
- Reactor contracts for individual farming pools
- User stakes and rewards
- Staking and reward events

### Project Structure

The `defi_space_indexer` package is organized as follows:

```
defi_space_indexer/
├── abi/                  # Contract ABI definitions
├── configs/              # Configuration variants
│   ├── dipdup.sqlite.yaml
│   ├── dipdup.compose.yaml
│   └── dipdup.swarm.yaml
├── deploy/               # Deployment configurations
├── handlers/             # Event handlers
│   ├── on_pair_created.py
│   ├── on_swap.py
│   ├── on_mint.py
│   └── ...
├── hooks/                # Periodic jobs and callbacks
│   ├── active_staking_window.py
│   └── ...
├── models/               # Data models
│   ├── amm_models.py
│   └── farming_models.py
├── sql/                  # SQL queries
├── types/                # Type definitions
├── dipdup.yaml           # Main configuration
└── env.example           # Environment variables template
```

Key components:
- **Handlers**: Process blockchain events (25+ event types)
- **Models**: Define data structures for AMM and Farming
- **Hooks**: Implement periodic jobs for metrics calculation
- **Configs**: Provide different deployment configurations

## 💻 API Examples

### 1. Get Most Profitable Pools
Find the most profitable pools based on fees, APY, and volume.

```typescript
async function getMostProfitablePools(minTVL: u256 = 10000) {
    const pools = await Pair.find({
        tvl_usd: { $gt: minTVL }
    })
    .sort({ apy_24h: -1 })
    .limit(10)
    .select({
        token0_address: 1,
        token1_address: 1,
        volume_24h: 1,
        tvl_usd: 1,
        apy_24h: 1,
        accumulated_fees_token0: 1,
        accumulated_fees_token1: 1
    });

    return pools.map(pool => ({
        pair: `${pool.token0_address}-${pool.token1_address}`,
        volume24h: pool.volume_24h,
        tvl: pool.tvl_usd,
        apy: pool.apy_24h,
        totalFees: {
            token0: pool.accumulated_fees_token0,
            token1: pool.accumulated_fees_token1
        }
    }));
}
```

### 2. Get User's Complete DeFi Position
Get a complete overview of a user's positions across both AMM and farming.

```typescript
async function getUserPositions(userAddress: ContractAddress) {
    // Get AMM positions
    const lpPositions = await LiquidityPosition.find({
        user_address: userAddress,
        liquidity: { $gt: 0 }
    }).populate('pair');

    // Get farming positions
    const farmPositions = await UserStake.find({
        user_address: userAddress,
        staked_amount: { $gt: 0 }
    }).populate({
        path: 'reactor',
        populate: { path: 'reward_data' }
    });

    return {
        liquidityPositions: lpPositions.map(pos => ({
            pair: pos.pair_address,
            liquidity: pos.liquidity,
            value: pos.usd_value,
            returns: {
                apy: pos.apy_earned,
                deposits: {
                    token0: pos.deposits_token0,
                    token1: pos.deposits_token1
                },
                withdrawals: {
                    token0: pos.withdrawals_token0,
                    token1: pos.withdrawals_token1
                }
            }
        })),
        farmingPositions: farmPositions.map(pos => ({
            farm: pos.reactor_address,
            staked: pos.staked_amount,
            pendingRewards: Object.entries(pos.rewards),
            canWithdraw: pos.penalty_end_time <= Date.now() / 1000
        })),
        totalValueLocked: lpPositions.reduce((sum, pos) => sum + pos.usd_value, 0)
    };
}
```

### 3. Protocol Overview
Get comprehensive protocol metrics for monitoring.

```typescript
async function getProtocolOverview() {
    const [factory, powerplant] = await Promise.all([
        Factory.findOne().sort({ created_at: -1 }),
        Powerplant.findOne().sort({ created_at: -1 })
    ]);

    // Get active pairs and reactors
    const [pairs, reactors] = await Promise.all([
        Pair.find(),
        Reactor.find()
    ]);

    // Calculate overall metrics
    const totalAMMTVL = pairs.reduce((sum, p) => sum + p.tvl_usd, 0);
    const totalFarmTVL = powerplant.total_value_locked;
    
    const largestPool = pairs.reduce(
        (max, p) => p.tvl_usd > max.tvl ? { address: p.pk, tvl: p.tvl_usd } : max,
        { address: '', tvl: 0 }
    );

    return {
        metrics: {
            totalValueLocked: totalAMMTVL + totalFarmTVL,
            activePairs: factory.num_of_pairs,
            activeFarms: powerplant.reactor_count,
            averageAPY: pairs.reduce((sum, p) => sum + p.apy_24h, 0) / pairs.length
        },
        topPool: {
            address: largestPool.address,
            tvlShare: (largestPool.tvl / totalAMMTVL) * 100
        },
        volume24h: pairs.reduce((sum, p) => sum + p.volume_24h, 0)
    };
}
```

## ⚡ Performance Considerations

- **Hardware Requirements**:
  - Minimum: 256 MB RAM, 1 CPU core
  - Recommended: 1GB+ RAM for average projects
  - Storage: Depends on indexed data volume
  - Note: RAM requirements increase with number of indexes

- **Optimization Tips**:
  - Use appropriate database indexes for frequent queries
  - Consider sharding for large datasets
  - Monitor memory usage during sync operations
  - Use batch processing for high-volume operations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

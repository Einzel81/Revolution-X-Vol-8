# Revolution X - Advanced AI Trading Platform v5.9

![Version](https://img.shields.io/badge/version-5.9.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

Revolution X is a professional-grade algorithmic trading platform powered by artificial intelligence, featuring multi-strategy execution, real-time risk management, and institutional-grade security.

## 🚀 Features

- **AI-Powered Trading**: LSTM, XGBoost, LightGBM ensemble models
- **Smart Money Concepts**: SMC, ICT, Volume Profile strategies
- **Risk Management**: AI Guardian, real-time monitoring
- **Multi-Platform**: Web, Mobile, Telegram integration
- **Security**: Bank-grade encryption, 2FA, audit logging

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

## 🛠️ Installation

### Quick Start (Docker)

```bash
# Clone repository
git clone https://github.com/Einzel81/Revolution-X---Vol-5.9.git
cd Revolution-X---Vol-5.9

# Copy environment file
cp .env.example .env

# Start services
docker-compose -f docker/docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Create admin user
docker-compose exec backend python scripts/create_admin.py

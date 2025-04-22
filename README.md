# Fraud Detection and Authentication System

A distributed microservices application for financial transaction management with fraud detection capabilities. The system consists of two main services:

1. **Authentication Service**: User authentication and token-based security
2. **Transaction Service**: Financial transaction management and fraud prediction

## System Requirements

- Python 3.8 or higher
- Virtual environment (venv)

## Quick Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
# source venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Iff errors, ensure critical dependencies are installed properly
pip install bcrypt>=3.2.2 aiohttp>=3.8.0
```

## Running the Services

Please refer to TEST_COMMANDS.MD



## Project Structure

```
.
├── auth_service/         # Authentication service
│   └── app/
│       ├── main.py       # API endpoints and service configuration
│       ├── auth.py       # Token generation and verification
│       ├── users.py      # User management
│       ├── models.py     # Data models
│       └── logger.py     # Logging configuration
│
├── transaction_service/  # Transaction service
│   └── app/
│       ├── main.py       # API endpoints and service configuration
│       ├── auth.py       # Token validation
│       ├── database.py   # Database connections and models
│       ├── models.py     # Data models
│       └── logger.py     # Logging configuration
│
├── requirements.txt      # Project dependencies
└── README.md             # This documentation
```

## Technology Choices

- **FastAPI**: High-performance asynchronous API framework
- **SQLAlchemy**: SQL toolkit and ORM for database interactions
- **SQLite**: Lightweight embedded database for transaction persistence
- **Passlib/bcrypt**: Secure password hashing
- **Python-jose**: JWT token generation and validation

## Common Issues

- If you encounter module import errors, ensure you're running using the module syntax (`python -m auth_service.app.main`)
- For Windows users, ensure bcrypt is properly installed with `pip install bcrypt>=3.2.2`

For detailed technical documentation, see [DOCUMENTATION.md](DOCUMENTATION.md). 


## Authors
- Nevin Joseph
- Abed Midani
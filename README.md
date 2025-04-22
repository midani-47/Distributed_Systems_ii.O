# Fraud Detection and Authentication System

This is a microservices architecture where each service is independent and communicates only through well-defined API interfaces.
A distributed application for financial transaction management with fraud detection capabilities. The system consists of two main services:

1. **Authentication Service**: User authentication and token-based security
2. **Transaction Service**: Financial transaction management and fraud prediction

## System Stack
- **FastAPI**: It was an interesting choice for us, because it was a new thing to explore for us. It is said to be fast comparable to others. While being easy to use and intuitive, it was still robust using Python type hints for data validation, serialization, and deserialization right out of the box, leading to fewer bugs.   
It automatically generates interactive API documentation (Swagger UI) based on our code. It has automatic OpenAPI documentation and native async support.

- For other technology stack choices, please refer 

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

# Please open two more terminals for initiating the services


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
├── documentation.txt      # Documentation
├── TEST_COMMANDS.md      # Testing commands
└── README.md             # This file
```

## Technology Choices

- **FastAPI**: High-performance asynchronous API framework
- **SQLAlchemy**: SQL toolkit and ORM for database interactions
- **SQLite**: Lightweight embedded database for transaction persistence
- **Passlib/bcrypt**: Secure password hashing


## Common Issues

- As we used two different OS (macOS and windows), we faced a couple of issues in PORTS, modules, and CLIs. Thus we ended up providing two CLI syntaxes and all OS compatible modules. Our test users managed PowerShell on windows.
- If you encounter module import errors, ensure you're running using the module syntax (`python -m auth_service.app.main`)
- For Windows users, ensure bcrypt is properly installed with `pip install bcrypt>=3.2.2`

For detailed technical documentation, see [DOCUMENTATION.md](DOCUMENTATION.md). 


## Authors
- Abed Midani
- Nevin Joseph

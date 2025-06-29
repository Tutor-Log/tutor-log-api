# FastAPI Server

This project is a simple FastAPI application that demonstrates how to set up a basic server with API routes.

## Project Structure

```
tutor-log-api
├── main.py              # Entry point of the FastAPI application
├── database.py          # Database configuration and table creation
├── routers/
│   └── base.py          # Base router that includes all API endpoints
├── models/
│   ├── __init__.py      # Model imports
│   ├── event_pupil.py   # Event-pupil relationship models
│   ├── events.py        # Event models for tutoring sessions
│   ├── groups.py        # Group models for organizing pupils
│   ├── payments.py      # Payment tracking models
│   ├── pupils.py        # Pupil/student models
│   └── users.py         # User models
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd tutor-log-api
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   fastapi dev main.py 
   ```

## Usage

Once the server is running, you can access the API at `http://127.0.0.1:8000`. You can also view the interactive API documentation at `http://127.0.0.1:8000/docs`.

## Features

This API provides functionality for:
- Managing tutoring events and sessions
- Tracking pupils/students information
- Organizing pupils into groups
- Recording and tracking payments
- User management
- Event-pupil relationships for session attendance

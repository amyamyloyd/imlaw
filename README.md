# ImLaw Document Management System

A comprehensive document management system for immigration law firms, featuring PDF form extraction, auto-filling, and client data management.

## Project Structure

```
imlaw/
├── backend/              # Python FastAPI backend service
│   ├── src/             # Source code
│   ├── tests/           # Test files
│   ├── requirements.txt # Python dependencies
│   └── setup.py        # Package configuration
├── frontend/            # React frontend
│   ├── src/            # React components
│   ├── public/         # Static assets
│   └── package.json    # Node dependencies
└── shared/             # Shared types/utilities
    └── types/          # TypeScript types
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm start
   ```

## Development

- Backend runs on FastAPI with MongoDB
- Frontend uses React with TypeScript
- PDF processing uses pdfplumber for extraction
- Form generation uses dynamic React components

## Testing

- Backend: `pytest` in the backend directory
- Frontend: `npm test` in the frontend directory

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## License

MIT 
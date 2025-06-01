# ImLaw Admin Frontend

This is the administrative interface for the ImLaw application, built with React, TypeScript, and Material-UI.

## Features

- Canonical Field Registry Management
- Form Field Mapping Interface
- Validation Rule Configuration
- Usage Statistics Viewing
- Material-UI Based Design

## Prerequisites

- Node.js (v18 or later)
- npm (v9 or later)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file in the root directory with the following content:
```env
VITE_API_BASE_URL=http://localhost:8000  # Update with your backend API URL
```

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Build

To create a production build:

```bash
npm run build
```

The build output will be in the `dist` directory.

## Development

### Project Structure

```
frontend/
├── docs/               # Documentation
├── src/               # Source code
│   ├── components/    # Reusable components
│   ├── pages/         # Page components
│   ├── types/         # TypeScript interfaces
│   ├── App.tsx        # Main application component
│   └── main.tsx       # Application entry point
├── public/            # Static assets
└── package.json       # Project configuration
```

### Key Technologies

- React 18
- TypeScript
- Material-UI
- React Router
- Vite

### Documentation

- [Admin UI Components](docs/admin-ui-components.md)

## Testing

Run the test suite:

```bash
npm run test
```

## Linting

Run ESLint:

```bash
npm run lint
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

This project is proprietary and confidential.

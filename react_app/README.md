#  React Application

A modern React web application featuring a sleek dark mode interface and interactive tree visualization.

## Features

- Modern, minimalist design with dark mode
- Interactive website visualization
- Smooth animations and transitions
- Support for JSON/XML file uploads
- Responsive tree visualization with zoom & pan functionality

## Running with Docker

To run the application, simply use:

```bash
docker build -t react-app .
docker run -p 1723:1723 react-app
```

The application will be available at `http://localhost:1723`

## Development

To run the application locally:

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

## Tech Stack

- React 18
- React Router for navigation
- Styled Components for styling
- Framer Motion for animations
- React Flow for tree visualization
- Docker for containerization

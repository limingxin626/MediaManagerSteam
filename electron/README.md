# Media Manager Electron App

This is an Electron application that wraps a Vue frontend and FastAPI backend.

## Prerequisites

- Node.js and npm
- Python 3.8+
- Vue 3 development environment

## Installation

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Build the Vue frontend**
   ```bash
   # In the vue directory
   npm run build
   ```

3. **Install Python dependencies**
   ```bash
   # In the backend directory
   pip install -r requirements.txt
   ```

## Development

1. **Start the Vue development server**
   ```bash
   # In the vue directory
   npm run dev
   ```

2. **Start the Electron app**
   ```bash
   # In the electron directory
   npm run dev
   ```

## Build for Production

1. **Build the Vue frontend**
   ```bash
   # In the vue directory
   npm run build
   ```

2. **Build the Electron app**
   ```bash
   # In the electron directory
   npm run build
   ```

## Project Structure

- `electron/` - Electron main process code
- `vue/` - Vue frontend code
- `backend/` - FastAPI backend code

## Notes

- The backend runs on port 8000
- The frontend runs on port 5173 in development mode
- In production, the frontend is served from the `vue-dist` directory
- The backend is bundled with the Electron app

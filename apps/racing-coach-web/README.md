# Racing Coach Web Dashboard

Modern web dashboard for analyzing racing telemetry data from iRacing sessions.

## Tech Stack

- **Framework**: Vite 7 + React 19 + TypeScript
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui (Radix UI primitives)
- **State Management**: TanStack Query v5 (React Query)
- **Routing**: React Router v7
- **API Client**: Orval (auto-generated from OpenAPI spec)
- **Charts**: Plotly.js for interactive telemetry visualization
- **Forms**: React Hook Form + Zod validation

## Features

### Current Pages

- **Sessions**: List and browse all racing sessions
- **Session Detail**: View individual session with lap breakdown
- **Lap Analysis**: Detailed telemetry charts for single lap
- **Lap Comparison**: Side-by-side comparison of two laps
- **Live Session**: Real-time updates via WebSocket (coming soon)

### Planned Features

- Interactive telemetry charts (speed, throttle, brake, steering)
- Corner-by-corner performance breakdown
- Braking zone analysis
- Delta comparison overlays
- Tire temperature and wear visualization
- Real-time session monitoring

## Development

### Prerequisites

- Node.js 20+
- npm or similar package manager
- Racing Coach Server running on localhost:8000

### Local Setup

\`\`\`bash
# Install dependencies
npm install

# Generate API client from OpenAPI spec
# (Make sure the server is running first!)
npm run generate:api

# Start dev server
npm run dev

# Visit http://localhost:3000
\`\`\`

### Available Scripts

- \`npm run dev\` - Start development server (port 3000)
- \`npm run build\` - Build for production
- \`npm run preview\` - Preview production build
- \`npm run lint\` - Lint code with ESLint
- \`npm run format\` - Format code with Prettier
- \`npm run generate:api\` - Generate TypeScript API client from OpenAPI

## Production Deployment

### Docker

\`\`\`bash
# Build the image
docker build -t racing-coach-web .

# Run the container
docker run -p 3000:80 racing-coach-web
\`\`\`

### Docker Compose

The app is included in the root docker-compose.yaml.

The web dashboard will be available at http://localhost:3000

## Architecture

The app uses Orval to auto-generate TypeScript types and React Query hooks from the FastAPI server's OpenAPI specification.

## License

See root LICENSE file.

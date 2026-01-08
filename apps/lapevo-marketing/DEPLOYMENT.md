# LapEvo Marketing Site - Cloudflare Pages Deployment

This site is deployed on Cloudflare Pages with D1 for data persistence.

## Architecture

- **Hosting**: Cloudflare Pages (serverless edge deployment)
- **Database**: Cloudflare D1 (SQLite-based serverless database)
- **Framework**: Astro 5 with Cloudflare adapter
- **API**: Server-side API routes at `/api/*`

## Prerequisites

1. [Cloudflare account](https://dash.cloudflare.com/sign-up) (free tier is sufficient)
2. [Node.js 22+](https://nodejs.org/)
3. npm (comes with Node.js)

---

## Initial Setup

### 1. Install Dependencies

```bash
cd apps/lapevo-marketing
npm install
```

This installs wrangler (Cloudflare CLI) as a dev dependency.

### 2. Authenticate with Cloudflare

```bash
npx wrangler login
```

This opens a browser window to authenticate. You only need to do this once.

### 3. Create D1 Database

```bash
npx wrangler d1 create lapevo-db
```

Copy the `database_id` from the output. It will look something like:

```
✅ Successfully created DB 'lapevo-db' in region WNAM
Created your new D1 database.

[[d1_databases]]
binding = "DB"
database_name = "lapevo-db"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  <-- Copy this!
```

### 4. Update wrangler.toml

Open `wrangler.toml` and replace `LOCAL_ONLY` with your actual database ID:

```toml
[[d1_databases]]
binding = "DB"
database_name = "lapevo-db"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # Your actual ID here
```

### 5. Run Database Migrations

```bash
# Apply to local development database
npm run db:migrate:local

# Apply to production database (after creating in step 3)
npm run db:migrate:remote
```

---

## Local Development

### Option A: Wrangler on Host (Recommended)

The simplest approach with full Cloudflare feature support:

```bash
cd apps/lapevo-marketing
npm install
npm run db:migrate:local  # First time only
npm run dev
```

Site available at: http://localhost:4321

### Option B: Docker Compose

For consistency with other services in the monorepo:

```bash
# From repo root
docker compose up lapevo-marketing
```

The Docker container runs wrangler internally with local D1 emulation.

**Note**: The first run may take longer as it initializes the D1 database.

### Accessing Local D1 Data

```bash
# View all waitlist entries
npx wrangler d1 execute lapevo-db --local --command "SELECT * FROM waitlist_entry"

# View all feature requests
npx wrangler d1 execute lapevo-db --local --command "SELECT * FROM feature_request"
```

---

## Production Deployment

### Manual Deployment

```bash
cd apps/lapevo-marketing

# Build the site
npm run build

# Deploy to Cloudflare Pages
npm run deploy
```

### Automated Deployment (GitHub Actions)

Deployments are automatic on push to `main` when files in `apps/lapevo-marketing/` change.

#### Required GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

| Secret                   | Description                       | How to Get                                                                                                     |
| ------------------------ | --------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `CLOUDFLARE_API_TOKEN`   | API token with Pages/D1 edit      | [Create token](https://dash.cloudflare.com/profile/api-tokens) with "Edit Cloudflare Workers" template         |
| `CLOUDFLARE_ACCOUNT_ID`  | Your Cloudflare account ID        | Found in dashboard URL: `dash.cloudflare.com/<ACCOUNT_ID>/...` or run `npx wrangler whoami`                    |

#### API Token Permissions Required

When creating your API token, use the "Edit Cloudflare Workers" template, which includes:

- Account: Cloudflare Pages (Edit)
- Account: D1 (Edit)
- Account: Workers Scripts (Edit)

### First-Time Pages Project Setup

If the Pages project doesn't exist yet, create it:

```bash
npx wrangler pages project create lapevo-marketing
```

Or it will be created automatically on first deploy.

---

## Custom Domain Setup

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com) → Pages → lapevo-marketing
2. Click "Custom domains" tab
3. Click "Set up a custom domain"
4. Enter your domain (e.g., `lapevo.com`)
5. Follow the DNS configuration instructions
6. SSL is provisioned automatically

---

## Database Management

### Viewing Data (D1 Console)

No admin UI is built into the site. Use Cloudflare Dashboard or wrangler CLI:

```bash
# Query waitlist entries
npx wrangler d1 execute lapevo-db --remote --command "SELECT * FROM waitlist_entry ORDER BY created_at DESC LIMIT 50"

# Query feature requests
npx wrangler d1 execute lapevo-db --remote --command "SELECT * FROM feature_request ORDER BY created_at DESC LIMIT 50"

# Count entries
npx wrangler d1 execute lapevo-db --remote --command "SELECT COUNT(*) as total FROM waitlist_entry"

# Export to JSON
npx wrangler d1 execute lapevo-db --remote --command "SELECT * FROM waitlist_entry" --json > waitlist_export.json
```

### Creating New Migrations

1. Create a new SQL file in the `migrations/` directory:

```bash
touch migrations/0002_your_change.sql
```

2. Write your SQL changes (use SQLite syntax)

3. Apply migrations:

```bash
# Test locally first
npm run db:migrate:local

# Then apply to production
npm run db:migrate:remote
```

---

## Database Schema

### waitlist_entry

| Column       | Type | Description                          |
| ------------ | ---- | ------------------------------------ |
| `id`         | TEXT | Primary key (UUID)                   |
| `email`      | TEXT | Unique email address                 |
| `source`     | TEXT | Where signup came from (e.g., "landing") |
| `ip_address` | TEXT | Client IP address                    |
| `created_at` | TEXT | ISO timestamp                        |

### feature_request

| Column              | Type | Description                          |
| ------------------- | ---- | ------------------------------------ |
| `id`                | TEXT | Primary key (UUID)                   |
| `waitlist_entry_id` | TEXT | FK to waitlist_entry (nullable)      |
| `email`             | TEXT | Email if provided (nullable)         |
| `content`           | TEXT | The feature request text             |
| `source`            | TEXT | Where request came from              |
| `ip_address`        | TEXT | Client IP address                    |
| `created_at`        | TEXT | ISO timestamp                        |

---

## Available Scripts

| Script               | Description                                          |
| -------------------- | ---------------------------------------------------- |
| `npm run dev`        | Start Astro dev server with D1 emulation (via platformProxy) |
| `npm run build`      | Build for production                                 |
| `npm run preview`    | Preview production build with wrangler               |
| `npm run db:migrate:local` | Apply migrations to local D1                   |
| `npm run db:migrate:remote` | Apply migrations to production D1             |
| `npm run deploy`     | Build and deploy to Cloudflare Pages                 |

---

## Monitoring & Logs

- **Logs**: Cloudflare Dashboard → Pages → lapevo-marketing → Functions → Real-time Logs
- **Analytics**: Cloudflare Dashboard → Pages → lapevo-marketing → Analytics
- **D1 Metrics**: Cloudflare Dashboard → D1 → lapevo-db → Metrics

---

## Troubleshooting

### "D1 database not found" locally

Run migrations first:

```bash
npm run db:migrate:local
```

### API routes returning 404

Ensure `astro.config.mjs` has server output and Cloudflare adapter:

```javascript
export default defineConfig({
  output: "server",
  adapter: cloudflare({ ... })
});
```

### Build fails with TypeScript errors

Ensure `@cloudflare/workers-types` is installed and `src/env.d.ts` has the correct types.

### Wrangler authentication issues

Re-authenticate:

```bash
npx wrangler logout
npx wrangler login
```

### Docker container not starting

Check that `WRANGLER_SEND_METRICS=false` is set. Wrangler prompts for metrics consent which freezes Docker.

---

## Cost

Cloudflare free tier includes:

- **Pages**: 500 builds/month, unlimited bandwidth, unlimited requests
- **D1**: 5GB storage, 5 million reads/day, 100,000 writes/day
- **Workers**: 100,000 requests/day

This is more than sufficient for a marketing site.

---

## Architecture Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   User Browser  │────▶│  Cloudflare Edge │────▶│   D1 (SQLite)│
│                 │     │  (Astro SSR)     │     │   Database   │
└─────────────────┘     └──────────────────┘     └─────────────┘
                              │
                              ▼
                        ┌──────────────────┐
                        │  /api/submit     │
                        │  (API Route)     │
                        └──────────────────┘
```

The site runs on Cloudflare's edge network globally. Form submissions go to the `/api/submit` endpoint which writes to D1.

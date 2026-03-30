# Maine Meeting Alerts

Internal BDN newsroom tool for monitoring Maine public meeting recordings. Submit a YouTube or Vimeo URL, get a transcript, and receive email alerts when topics you cover are discussed.

## How It Works

1. **Submit** a meeting video URL (YouTube/Vimeo)
2. **yt-dlp** downloads the audio
3. **OpenAI Whisper** transcribes it with timestamps
4. **Claude** checks the transcript against your alert topics (semantic matching, not just keywords)
5. **Email notification** sent when your topics are discussed
6. **Claude + Nota** generate a structured meeting summary and key points

## Tech Stack

- **Next.js 16** (App Router, TypeScript) — frontend + API
- **PostgreSQL** — meetings, transcripts, users, alerts
- **Redis + BullMQ** — background job queue for transcription & analysis
- **OpenAI Whisper API** — speech-to-text (~$1.08/3hr meeting)
- **Claude API** — topic matching & structured summaries
- **Nota API** (optional) — key-point bullet summaries
- **Resend** — email notifications
- **Prisma 7** — database ORM

## Setup

### Prerequisites

- Node.js 20+
- Docker (for PostgreSQL and Redis)
- yt-dlp installed (`brew install yt-dlp` or `pip install yt-dlp`)
- ffmpeg installed (`brew install ffmpeg`)

### Install & Run

```bash
# Install dependencies
npm install

# Start PostgreSQL and Redis
docker compose up -d

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Create database tables
npm run db:migrate

# Start the web app
npm run dev

# In a separate terminal, start the background workers
npm run workers
```

### Environment Variables

See `.env.example` for all required variables. At minimum you need:

- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `OPENAI_API_KEY` — for Whisper transcription
- `ANTHROPIC_API_KEY` — for Claude topic matching & summaries
- `RESEND_API_KEY` — for email notifications

Optional:
- `NOTA_API_URL` / `NOTA_API_KEY` — for Nota key-point summaries

## Usage

1. Open `http://localhost:3000`
2. Go to **My Alerts** and create alert rules for topics you cover
3. Go to **Submit Meeting** and paste a YouTube/Vimeo URL
4. The system transcribes, analyzes, and emails you if your topics come up

## Project Structure

```
src/
├── app/                    # Next.js pages & API routes
│   ├── api/meetings/       # Meeting CRUD + transcription trigger
│   ├── api/alerts/         # Alert rule CRUD
│   ├── api/users/          # User management
│   ├── meetings/           # Meeting list, detail, submission pages
│   └── alerts/             # Alert rule management page
├── workers/                # Background job processors
│   ├── transcription.ts    # yt-dlp → Whisper → DB
│   ├── alert-matcher.ts    # Claude topic matching → email
│   └── summarizer.ts       # Claude + Nota summaries
├── lib/                    # Shared clients & utilities
│   ├── db.ts               # Prisma client
│   ├── queue.ts            # BullMQ queues
│   ├── whisper.ts          # OpenAI Whisper API
│   ├── claude.ts           # Anthropic Claude API
│   ├── nota.ts             # Nota API
│   └── email.ts            # Resend email
└── generated/prisma/       # Generated Prisma client
```

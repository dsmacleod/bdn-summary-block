# BDN Headline Test

A/B/Y headline testing plugin for WordPress/Newspack. Tests run automatically and resolve via GA4 analytics — the winning headline replaces the original post title.

## Installation

```bash
composer install
npm install
npm run build
```

Activate **BDN Headline Test** in the WordPress plugins screen.

## Configuration

Go to **Tools > Headline Test Settings** and fill in:

| Setting | Description | Default |
|---------|-------------|---------|
| GA4 Property ID | Your GA4 property (e.g. `properties/123456789`) | — |
| Service Account JSON | Paste the full JSON key for your Google service account | — |
| Minimum Impressions | Impressions required before a test can resolve | 1000 |
| Maximum Duration | Hours before a test auto-resolves regardless of significance | 72 |

## Usage

### From the post editor

1. Open the **Headline Test** sidebar panel.
2. Enter a **Variant B** headline (and optionally **Variant C**).
3. Toggle the test **on** and publish/update the post.

### From the dashboard

Go to **Tools > Headline Tests** to view all active and completed tests, pause/resume tests, or manually declare a winner.

## How Auto-Resolution Works

1. An hourly WP-Cron job fires and queries the **GA4 Data API** for each active test.
2. For each variant, the plugin calculates **CTR** (clicks / impressions).
3. Once minimum impressions are met, a **chi-squared test** is applied.
4. If one variant wins at **p < 0.05**, it is declared the winner and the post title is updated automatically.
5. If no winner emerges by the maximum duration, the best-performing variant is selected.

## GA4 Setup

1. **Create custom dimensions** in your GA4 property:
   - `post_id` (event-scoped) — the WordPress post ID
   - `variant_id` (event-scoped) — the headline variant being shown (e.g. `A`, `B`, `C`)
2. **Create a service account** in Google Cloud Console with access to your GA4 property.
3. Grant the service account **Viewer** role on the GA4 property (Admin > Property Access Management).
4. Download the JSON key and paste it into the plugin settings.

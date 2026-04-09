# BDN Headline A/B Test

A WordPress plugin for A/B/Y headline testing on Newspack-powered news sites. Editors enter 2-3 headline variants per post; the plugin randomly shows variants to readers, tracks clicks via Google Analytics 4, and automatically promotes the winner.

## How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│ Post Editor  │────▶│  WordPress/PHP   │────▶│  Frontend   │
│ Sidebar UI   │     │  Title Filter    │     │  JS Swap    │
│ (variants)   │     │  (data attrs)    │     │  (localStorage)
└─────────────┘     └──────────────────┘     └──────┬──────┘
                                                     │
                                              GA4 events
                                              (impression/click)
                                                     │
                    ┌──────────────────┐              ▼
                    │  WP-Cron (hourly)│◀──── GA4 Data API
                    │  Chi-squared test│
                    │  Declare winner  │
                    └──────────────────┘
```

1. **Editor enters variants** in the Gutenberg sidebar panel (Variant A = current title, B and C are alternatives)
2. **Title filter** injects `data-headline-test` attributes into headline HTML on the frontend
3. **Frontend JS** (~2KB, async) assigns each visitor a sticky variant via localStorage, swaps the headline text, and fires GA4 custom events (`headline_test_impression`, `headline_test_click`)
4. **Anti-flash CSS** hides tested headlines until JS resolves them (500ms fallback for no-JS)
5. **Hourly WP-Cron** queries GA4 Data API, calculates CTR per variant, applies a chi-squared significance test (p < 0.05), and declares the winner — updating `post_title` automatically
6. If no statistically significant winner emerges within the max duration (default 72h), the highest-CTR variant wins

## Installation

```bash
cd wp-content/plugins/
git clone https://github.com/dsmacleod/headline-test.git bdn-headline-test
cd bdn-headline-test
composer install
npm install
npm run build
```

Activate **BDN Headline A/B Test** in the WordPress admin.

## Configuration

Navigate to **Tools > Headline Test Settings**:

| Setting | Description | Default |
|---------|-------------|---------|
| GA4 Property ID | Your GA4 property ID (numeric, e.g. `123456789`) | — |
| Service Account JSON | Full JSON key for a Google service account with GA4 read access | — |
| Minimum Impressions | Impressions per variant required before evaluating significance | 1,000 |
| Maximum Duration | Hours before auto-resolving regardless of significance | 72 |

### GA4 Setup

1. In your GA4 property, create two **event-scoped custom dimensions**:
   - Parameter name: `post_id` — the WordPress post ID
   - Parameter name: `variant_id` — the variant shown (`a`, `b`, or `c`)
2. In Google Cloud Console, create a **service account** and download its JSON key
3. In GA4 Admin > Property Access Management, grant the service account **Viewer** access
4. Paste the JSON key into the plugin settings

## Usage

### Post Editor

1. Open any post in the block editor
2. Find the **Headline Test** panel in the document sidebar
3. Enter a **Variant B** headline (and optionally **Variant C**)
4. Toggle **Start test** and save/publish the post
5. When a winner is declared, the panel shows the result

### Dashboard

**Tools > Headline Tests** shows a table of all active and completed tests with:
- Post title and link to editor
- All variant texts
- Current status (Active / Completed / Paused)
- Winning variant (when resolved)

## Plugin Structure

```
bdn-headline-test/
├── bdn-headline-test.php          # Main plugin file, autoloader
├── includes/
│   ├── class-settings.php         # Plugin settings (wp_options)
│   ├── class-post-meta.php        # Post meta registration
│   ├── class-title-filter.php     # Injects data attributes on frontend titles
│   ├── class-frontend-assets.php  # Enqueues JS, injects anti-flash CSS
│   ├── class-admin-page.php       # Test dashboard (Tools > Headline Tests)
│   ├── class-ga4-client.php       # GA4 Data API client + chi-squared test
│   └── class-cron-resolver.php    # Hourly evaluation + winner declaration
├── src/
│   ├── frontend/index.js          # Headline swap + GA4 event tracking
│   └── editor/index.js            # Gutenberg sidebar panel (React)
├── tests/
│   ├── bootstrap.php
│   ├── test-settings.php
│   ├── test-post-meta.php
│   ├── test-title-filter.php
│   ├── test-frontend-assets.php
│   ├── test-admin-page.php
│   ├── test-ga4-client.php
│   ├── test-cron-resolver.php
│   └── test-integration.php
├── composer.json
├── package.json
├── phpunit.xml.dist
└── webpack.config.js
```

## Requirements

- WordPress 6.4+
- PHP 8.1+
- Google Analytics 4 with Data API access
- Node.js (for building editor/frontend JS)

## Development

```bash
# Watch mode for JS development
npm run start

# Run PHP tests (requires WP test environment)
vendor/bin/phpunit
```

## License

Proprietary — Bangor Daily News.

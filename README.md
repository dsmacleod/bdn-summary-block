# BDN Summary Block

WordPress plugin that adds a `bdn/story-summary` Gutenberg block to the block editor. The block displays a concise "In brief" bullet-point summary at the top of a story, generated on demand using the [Nota](https://www.nota.ai) key-points API. Editors review and edit the bullets before publishing.

## What it does

- Registers the `bdn/story-summary` block in the Gutenberg editor
- In the **empty state**: shows a "Generate summary" button — one click calls Nota's key-points API and populates 3–4 editable bullet points
- In the **populated state**: each bullet is independently editable, with add/remove controls (min 2, max 6) and a Regenerate button in the block toolbar
- On the **frontend**: renders a styled "In brief" box with bullets and an AI attribution line that links to the newsroom's AI policy page
- The block is inserted automatically at the top of every imported story by the [bdn-metadata](https://github.com/dsmacleod/bdn-metadata) plugin

## Requirements

- WordPress 6.4+
- PHP 8.1+
- [Nota](https://www.nota.ai) plugin — already installed and configured with `nota_api_key` and `nota_api_url` options (this plugin reads those directly; no new credentials needed)
- Node.js 18+ and npm (only needed to rebuild JavaScript from source)

## Installation

The `build/` directory is committed to this repo, so no local build step is required on the server.

1. Upload the `bdn-summary-block` folder to `wp-content/plugins/`
2. Activate the plugin in **Plugins → Installed Plugins**
3. Go to **Settings → BDN Summary Block** and set the AI policy URL

## Configuration

**Settings → BDN Summary Block**

| Setting | Description |
|---|---|
| AI Policy URL | URL of the newsroom's AI policy page. Appears as a "Read our AI policy." link in the attribution line of every published summary block. Leave blank to omit the link. |

Nota API credentials are read automatically from the options set by the Nota plugin (`nota_api_key`, `nota_api_url`). No additional configuration is needed.

## Editor workflow

1. Open a post in the block editor. If imported via Docs-to-WordPress with bdn-metadata active, the block is already inserted at the top. Otherwise, add it from the block inserter under **Text → Story Summary**.
2. Click **Generate summary**. A spinner appears while the Nota API processes the story content. The block populates with 3–4 bullet points.
3. Review and edit the bullets as needed. Each bullet is a free-text field. You can add bullets (up to 6) or remove them (down to 2) using the inline controls.
4. To regenerate from scratch, click the **Regenerate summary** button in the block toolbar.
5. Publish. The "In brief" box and attribution line appear on the frontend automatically.

The block can be deleted from any post where a summary isn't appropriate.

## Frontend output

```
┌─ In brief ─────────────────────────────────────┐
│                                                 │
│  • Bullet one                                   │
│  • Bullet two                                   │
│  • Bullet three                                 │
│                                                 │
│  ─────────────────────────────────────────────  │
│  Generated with the help of AI.                 │
│  Read our AI policy.  [link]                    │
└─────────────────────────────────────────────────┘
```

Styled with a light gray background, a blue left border, and a small-caps "In brief" label. The attribution line is italic, smaller text — present but unobtrusive, similar to a photo credit.

## Development

To modify the JavaScript or SCSS, rebuild with:

```bash
npm install
npm run build
```

Commit the `build/` directory along with your source changes. The build output must be committed so the plugin works on servers without Node.

```bash
npm run lint:js     # ESLint
```

## Running tests

PHP tests use [wp-phpunit/wp-phpunit](https://github.com/wp-phpunit/wp-phpunit):

```bash
composer install
WP_TESTS_DIR=vendor/wp-phpunit/wp-phpunit vendor/bin/phpunit
```

## File structure

```
bdn-summary-block/
├── bdn-summary-block.php          ← Plugin entry point, autoloader, hook registration
├── includes/
│   ├── class-summary-settings.php ← Settings page (AI policy URL)
│   └── class-summary-ajax.php     ← AJAX handler, Nota API call, block data localization
├── src/
│   ├── block.json                 ← Block metadata and attribute schema
│   ├── index.js                   ← Block registration
│   ├── edit.js                    ← Editor UI (empty state + populated state)
│   ├── save.js                    ← Returns null (dynamic block, PHP renders frontend)
│   ├── render.php                 ← Server-side frontend render
│   └── style.scss                 ← Frontend + editor styles
├── build/                         ← Compiled output (committed; do not edit directly)
├── tests/
│   ├── bootstrap.php
│   ├── test-summary-settings.php
│   └── test-summary-ajax.php
├── composer.json
├── package.json
└── phpunit.xml.dist
```

## Related plugins

- **[bdn-metadata](https://github.com/dsmacleod/bdn-metadata)** — automatically inserts the empty `bdn/story-summary` block at the top of every imported story. Not required to use the block manually, but needed for the auto-insert workflow.

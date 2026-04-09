# Headline A/B/Y Testing Plugin — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** WordPress plugin that lets editors test 2-3 headline variants per post, tracks CTR via GA4, and auto-promotes the winner.

**Architecture:** Post meta stores variants. A `the_title` filter injects `data-headline-test` attributes. A ~2KB frontend JS swaps headlines and fires GA4 events. A WP-Cron job queries GA4 Data API hourly and resolves tests by statistical significance.

**Tech Stack:** PHP 8.1+, WordPress 6.4+, `@wordpress/scripts` for Gutenberg sidebar panel, vanilla JS for frontend swap, Google Analytics Data API v1 (via `google/analytics-data` composer package).

---

### Task 1: Plugin Scaffold

**Files:**
- Create: `cms-project/bdn-headline-test/bdn-headline-test.php`
- Create: `cms-project/bdn-headline-test/composer.json`
- Create: `cms-project/bdn-headline-test/package.json`
- Create: `cms-project/bdn-headline-test/phpunit.xml.dist`
- Create: `cms-project/bdn-headline-test/tests/bootstrap.php`

**Step 1: Create the main plugin file with autoloader**

```php
<?php
/**
 * Plugin Name: BDN Headline A/B Test
 * Description: A/B/Y headline testing with GA4 tracking and auto-resolution.
 * Version: 1.0.0
 * Author: Dan MacLeod with Claude Code
 * Requires at least: 6.4
 * Requires PHP: 8.1
 * Text Domain: bdn-headline-test
 */

defined( 'ABSPATH' ) || exit;

define( 'BDN_HT_DIR', plugin_dir_path( __FILE__ ) );
define( 'BDN_HT_URL', plugin_dir_url( __FILE__ ) );

spl_autoload_register( function ( string $class ): void {
    $prefix = 'BDN_Headline_Test\\';
    if ( ! str_starts_with( $class, $prefix ) ) {
        return;
    }
    $relative = str_replace( '\\', '/', substr( $class, strlen( $prefix ) ) );
    $file = BDN_HT_DIR . 'includes/class-' . strtolower( str_replace( '_', '-', $relative ) ) . '.php';
    if ( file_exists( $file ) ) {
        require_once $file;
    }
} );

add_action( 'plugins_loaded', function (): void {
    $settings = new BDN_Headline_Test\Settings();
    $settings->register();

    ( new BDN_Headline_Test\Post_Meta() )->register();
    ( new BDN_Headline_Test\Title_Filter() )->register();
    ( new BDN_Headline_Test\Frontend_Assets() )->register();
    ( new BDN_Headline_Test\Cron_Resolver( $settings ) )->register();
    ( new BDN_Headline_Test\Admin_Page() )->register();
} );
```

**Step 2: Create composer.json**

```json
{
    "require": {
        "google/analytics-data": "^0.12"
    },
    "require-dev": {
        "phpunit/phpunit": "^10",
        "wp-phpunit/wp-phpunit": "^6"
    },
    "autoload": {
        "psr-4": {
            "BDN_Headline_Test\\": "includes/"
        }
    }
}
```

**Step 3: Create package.json**

```json
{
    "name": "bdn-headline-test",
    "version": "1.0.0",
    "description": "BDN Headline A/B Test",
    "private": true,
    "scripts": {
        "build": "wp-scripts build",
        "start": "wp-scripts start"
    },
    "devDependencies": {
        "@wordpress/scripts": "^30.0.0"
    },
    "dependencies": {
        "@wordpress/plugins": "^7.0.0",
        "@wordpress/edit-post": "^8.0.0",
        "@wordpress/components": "^28.0.0",
        "@wordpress/data": "^10.0.0",
        "@wordpress/element": "^6.0.0",
        "@wordpress/i18n": "^5.0.0",
        "@wordpress/api-fetch": "^7.0.0"
    }
}
```

**Step 4: Create phpunit.xml.dist**

```xml
<?xml version="1.0"?>
<phpunit bootstrap="tests/bootstrap.php" colors="true">
    <testsuites>
        <testsuite name="BDN Headline Test">
            <directory>tests</directory>
        </testsuite>
    </testsuites>
</phpunit>
```

**Step 5: Create tests/bootstrap.php**

```php
<?php
$wp_tests_dir = getenv( 'WP_TESTS_DIR' )
    ?: dirname( __DIR__ ) . '/vendor/wp-phpunit/wp-phpunit';
require_once $wp_tests_dir . '/includes/functions.php';

tests_add_filter( 'muplugins_loaded', function (): void {
    require dirname( __DIR__ ) . '/bdn-headline-test.php';
} );

require_once $wp_tests_dir . '/includes/bootstrap.php';
```

**Step 6: Commit**

```bash
git add cms-project/bdn-headline-test/
git commit -m "feat(headline-test): plugin scaffold with autoloader and test bootstrap"
```

---

### Task 2: Settings Class

**Files:**
- Create: `cms-project/bdn-headline-test/includes/class-settings.php`
- Create: `cms-project/bdn-headline-test/tests/test-settings.php`

**Step 1: Write the failing test**

```php
<?php

class Test_Settings extends WP_UnitTestCase {

    public function test_defaults(): void {
        $settings = new BDN_Headline_Test\Settings();
        $this->assertSame( 1000, $settings->get( 'min_impressions' ) );
        $this->assertSame( 72, $settings->get( 'max_duration_hours' ) );
        $this->assertSame( '', $settings->get( 'ga4_property_id' ) );
        $this->assertSame( '', $settings->get( 'ga4_credentials_json' ) );
    }

    public function test_get_returns_saved_value(): void {
        update_option( 'bdn_ht_min_impressions', 500 );
        $settings = new BDN_Headline_Test\Settings();
        $this->assertSame( 500, $settings->get( 'min_impressions' ) );
    }
}
```

**Step 2: Run test to verify it fails**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Settings`
Expected: FAIL — class not found

**Step 3: Write minimal implementation**

```php
<?php

namespace BDN_Headline_Test;

class Settings {

    private const DEFAULTS = [
        'min_impressions'      => 1000,
        'max_duration_hours'   => 72,
        'ga4_property_id'      => '',
        'ga4_credentials_json' => '',
    ];

    public function register(): void {
        add_action( 'admin_menu', [ $this, 'add_menu' ] );
        add_action( 'admin_init', [ $this, 'register_settings' ] );
    }

    public function get( string $key ): mixed {
        $default = self::DEFAULTS[ $key ] ?? '';
        $value   = get_option( "bdn_ht_{$key}", $default );
        if ( is_int( $default ) ) {
            return (int) $value;
        }
        return $value;
    }

    public function add_menu(): void {
        add_submenu_page(
            'tools.php',
            'Headline A/B Tests',
            'Headline Tests',
            'manage_options',
            'bdn-headline-test',
            [ $this, 'render_page' ],
        );
    }

    public function register_settings(): void {
        foreach ( array_keys( self::DEFAULTS ) as $key ) {
            register_setting( 'bdn_headline_test', "bdn_ht_{$key}" );
        }
    }

    public function render_page(): void {
        // Placeholder — Task 7 builds the full admin page.
        echo '<div class="wrap"><h1>Headline A/B Tests</h1></div>';
    }
}
```

**Step 4: Run test to verify it passes**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Settings`
Expected: PASS

**Step 5: Commit**

```bash
git add cms-project/bdn-headline-test/includes/class-settings.php cms-project/bdn-headline-test/tests/test-settings.php
git commit -m "feat(headline-test): settings class with defaults and wp_options storage"
```

---

### Task 3: Post Meta Registration

**Files:**
- Create: `cms-project/bdn-headline-test/includes/class-post-meta.php`
- Create: `cms-project/bdn-headline-test/tests/test-post-meta.php`

**Step 1: Write the failing test**

```php
<?php

class Test_Post_Meta extends WP_UnitTestCase {

    public function set_up(): void {
        parent::set_up();
        ( new BDN_Headline_Test\Post_Meta() )->register();
    }

    public function test_variants_meta_registered(): void {
        $this->assertTrue(
            registered_meta_key_exists( 'post', '_headline_variants', 'post' )
        );
    }

    public function test_save_and_retrieve_variants(): void {
        $post_id  = self::factory()->post->create();
        $variants = [
            [ 'id' => 'a', 'text' => 'Original' ],
            [ 'id' => 'b', 'text' => 'Alternative' ],
        ];
        update_post_meta( $post_id, '_headline_variants', wp_json_encode( $variants ) );
        $stored = json_decode( get_post_meta( $post_id, '_headline_variants', true ), true );
        $this->assertSame( 'Alternative', $stored[1]['text'] );
    }

    public function test_status_defaults_empty(): void {
        $post_id = self::factory()->post->create();
        $this->assertSame( '', get_post_meta( $post_id, '_headline_test_status', true ) );
    }
}
```

**Step 2: Run test to verify it fails**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Post_Meta`
Expected: FAIL — class not found

**Step 3: Write minimal implementation**

```php
<?php

namespace BDN_Headline_Test;

class Post_Meta {

    public function register(): void {
        add_action( 'init', [ $this, 'register_meta' ] );
    }

    public function register_meta(): void {
        $meta_keys = [
            '_headline_variants'   => [
                'type'         => 'string',
                'description'  => 'JSON array of headline variants',
                'single'       => true,
                'show_in_rest' => true,
            ],
            '_headline_test_status' => [
                'type'         => 'string',
                'description'  => 'Test status: active, completed, paused',
                'single'       => true,
                'show_in_rest' => true,
            ],
            '_headline_test_winner' => [
                'type'         => 'string',
                'description'  => 'Winning variant ID',
                'single'       => true,
                'show_in_rest' => true,
            ],
        ];

        foreach ( $meta_keys as $key => $args ) {
            register_post_meta( 'post', $key, array_merge( $args, [
                'auth_callback' => function () {
                    return current_user_can( 'edit_posts' );
                },
            ] ) );
        }
    }
}
```

**Step 4: Run test to verify it passes**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Post_Meta`
Expected: PASS

**Step 5: Commit**

```bash
git add cms-project/bdn-headline-test/includes/class-post-meta.php cms-project/bdn-headline-test/tests/test-post-meta.php
git commit -m "feat(headline-test): register post meta for variants, status, winner"
```

---

### Task 4: Title Filter (data attribute injection)

**Files:**
- Create: `cms-project/bdn-headline-test/includes/class-title-filter.php`
- Create: `cms-project/bdn-headline-test/tests/test-title-filter.php`

**Step 1: Write the failing test**

```php
<?php

class Test_Title_Filter extends WP_UnitTestCase {

    private int $post_id;

    public function set_up(): void {
        parent::set_up();
        ( new BDN_Headline_Test\Post_Meta() )->register();
        do_action( 'init' );
        ( new BDN_Headline_Test\Title_Filter() )->register();

        $this->post_id = self::factory()->post->create( [ 'post_title' => 'Original' ] );
    }

    public function test_no_attribute_without_active_test(): void {
        $title = apply_filters( 'the_title', 'Original', $this->post_id );
        $this->assertStringNotContainsString( 'data-headline-test', $title );
    }

    public function test_adds_attribute_with_active_test(): void {
        $variants = wp_json_encode( [
            [ 'id' => 'a', 'text' => 'Original' ],
            [ 'id' => 'b', 'text' => 'Alt Headline' ],
        ] );
        update_post_meta( $this->post_id, '_headline_variants', $variants );
        update_post_meta( $this->post_id, '_headline_test_status', 'active' );

        $title = apply_filters( 'the_title', 'Original', $this->post_id );
        $this->assertStringContainsString( 'data-headline-test', $title );
        $this->assertStringContainsString( (string) $this->post_id, $title );
    }

    public function test_no_attribute_in_admin(): void {
        set_current_screen( 'edit-post' );
        $variants = wp_json_encode( [
            [ 'id' => 'a', 'text' => 'Original' ],
            [ 'id' => 'b', 'text' => 'Alt' ],
        ] );
        update_post_meta( $this->post_id, '_headline_variants', $variants );
        update_post_meta( $this->post_id, '_headline_test_status', 'active' );

        $title = apply_filters( 'the_title', 'Original', $this->post_id );
        $this->assertStringNotContainsString( 'data-headline-test', $title );
        set_current_screen( 'front' );
    }
}
```

**Step 2: Run test to verify it fails**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Title_Filter`
Expected: FAIL — class not found

**Step 3: Write minimal implementation**

```php
<?php

namespace BDN_Headline_Test;

class Title_Filter {

    public function register(): void {
        add_filter( 'the_title', [ $this, 'inject_data_attribute' ], 10, 2 );
    }

    public function inject_data_attribute( string $title, int $post_id ): string {
        if ( is_admin() ) {
            return $title;
        }

        $status = get_post_meta( $post_id, '_headline_test_status', true );
        if ( 'active' !== $status ) {
            return $title;
        }

        $variants_json = get_post_meta( $post_id, '_headline_variants', true );
        if ( empty( $variants_json ) ) {
            return $title;
        }

        $variants_attr = esc_attr( $variants_json );

        return sprintf(
            '<span data-headline-test="%d" data-headline-variants="%s">%s</span>',
            $post_id,
            $variants_attr,
            $title
        );
    }
}
```

**Step 4: Run test to verify it passes**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Title_Filter`
Expected: PASS

**Step 5: Commit**

```bash
git add cms-project/bdn-headline-test/includes/class-title-filter.php cms-project/bdn-headline-test/tests/test-title-filter.php
git commit -m "feat(headline-test): title filter injects data attributes for active tests"
```

---

### Task 5: Frontend JS — Headline Swap & GA4 Events

**Files:**
- Create: `cms-project/bdn-headline-test/src/frontend/index.js`
- Create: `cms-project/bdn-headline-test/includes/class-frontend-assets.php`
- Create: `cms-project/bdn-headline-test/tests/test-frontend-assets.php`

**Step 1: Write the frontend JS**

```js
/**
 * Headline A/B Test — frontend swap + GA4 tracking.
 * ~2KB minified. Loaded async on frontend only.
 */
( function () {
    'use strict';

    const STORAGE_PREFIX = 'bdn_ht_';

    function getAssignment( postId, variantCount ) {
        const key = STORAGE_PREFIX + postId;
        let assignment = localStorage.getItem( key );
        if ( assignment && parseInt( assignment, 10 ) < variantCount ) {
            return parseInt( assignment, 10 );
        }
        assignment = Math.floor( Math.random() * variantCount );
        localStorage.setItem( key, assignment );
        return assignment;
    }

    function fireGA4Event( eventName, postId, variantId ) {
        if ( typeof gtag === 'function' ) {
            gtag( 'event', eventName, {
                post_id: String( postId ),
                variant_id: variantId,
            } );
        }
    }

    function init() {
        const elements = document.querySelectorAll( '[data-headline-test]' );
        if ( ! elements.length ) {
            return;
        }

        elements.forEach( function ( el ) {
            const postId = parseInt( el.getAttribute( 'data-headline-test' ), 10 );
            const variants = JSON.parse( el.getAttribute( 'data-headline-variants' ) );
            const index = getAssignment( postId, variants.length );
            const variant = variants[ index ];

            el.textContent = variant.text;
            el.classList.add( 'ht-resolved' );

            fireGA4Event( 'headline_test_impression', postId, variant.id );

            // Find the closest link ancestor to track clicks.
            const link = el.closest( 'a' );
            if ( link ) {
                link.addEventListener( 'click', function () {
                    fireGA4Event( 'headline_test_click', postId, variant.id );
                }, { once: true } );
            }
        } );
    }

    if ( document.readyState === 'loading' ) {
        document.addEventListener( 'DOMContentLoaded', init );
    } else {
        init();
    }
} )();
```

**Step 2: Write the failing PHP test for asset enqueue**

```php
<?php

class Test_Frontend_Assets extends WP_UnitTestCase {

    public function test_script_not_enqueued_in_admin(): void {
        set_current_screen( 'edit-post' );
        ( new BDN_Headline_Test\Frontend_Assets() )->register();
        do_action( 'wp_enqueue_scripts' );
        $this->assertFalse( wp_script_is( 'bdn-headline-test-frontend', 'enqueued' ) );
        set_current_screen( 'front' );
    }
}
```

**Step 3: Write the PHP class**

```php
<?php

namespace BDN_Headline_Test;

class Frontend_Assets {

    public function register(): void {
        add_action( 'wp_enqueue_scripts', [ $this, 'enqueue' ] );
        add_action( 'wp_head', [ $this, 'anti_flash_css' ], 1 );
    }

    public function enqueue(): void {
        $asset_file = BDN_HT_DIR . 'build/frontend/index.asset.php';
        $asset      = file_exists( $asset_file ) ? require $asset_file : [
            'dependencies' => [],
            'version'      => '1.0.0',
        ];

        wp_enqueue_script(
            'bdn-headline-test-frontend',
            BDN_HT_URL . 'build/frontend/index.js',
            $asset['dependencies'],
            $asset['version'],
            [ 'strategy' => 'async', 'in_footer' => true ]
        );
    }

    public function anti_flash_css(): void {
        echo '<style>'
            . '[data-headline-test]{visibility:hidden}'
            . '[data-headline-test].ht-resolved{visibility:visible}'
            . '@keyframes ht-fallback{to{visibility:visible}}'
            . '[data-headline-test]{animation:ht-fallback 0s 0.5s forwards}'
            . '</style>';
    }
}
```

**Step 4: Update webpack config for multiple entry points**

Create `cms-project/bdn-headline-test/webpack.config.js`:

```js
const defaultConfig = require( '@wordpress/scripts/config/webpack.config' );
const path = require( 'path' );

module.exports = {
    ...defaultConfig,
    entry: {
        'frontend/index': path.resolve( __dirname, 'src/frontend/index.js' ),
        'editor/index': path.resolve( __dirname, 'src/editor/index.js' ),
    },
};
```

**Step 5: Run test to verify it passes**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Frontend_Assets`
Expected: PASS

**Step 6: Commit**

```bash
git add cms-project/bdn-headline-test/src/frontend/ cms-project/bdn-headline-test/includes/class-frontend-assets.php cms-project/bdn-headline-test/tests/test-frontend-assets.php cms-project/bdn-headline-test/webpack.config.js
git commit -m "feat(headline-test): frontend JS swap, GA4 events, anti-flash CSS"
```

---

### Task 6: Gutenberg Sidebar Panel

**Files:**
- Create: `cms-project/bdn-headline-test/src/editor/index.js`

**Step 1: Write the editor sidebar panel**

```jsx
import { registerPlugin } from '@wordpress/plugins';
import { PluginDocumentSettingPanel } from '@wordpress/edit-post';
import { TextControl, ToggleControl, Notice } from '@wordpress/components';
import { useSelect, useDispatch } from '@wordpress/data';
import { useEntityProp } from '@wordpress/core-data';
import { __ } from '@wordpress/i18n';

function HeadlineTestPanel() {
    const postType = useSelect( ( select ) =>
        select( 'core/editor' ).getCurrentPostType()
    );

    if ( postType !== 'post' ) {
        return null;
    }

    const [ meta, setMeta ] = useEntityProp( 'postType', 'post', 'meta' );

    const title = useSelect( ( select ) =>
        select( 'core/editor' ).getEditedPostAttribute( 'title' )
    );

    const variantsRaw = meta._headline_variants || '[]';
    const variants = JSON.parse( variantsRaw );
    const status = meta._headline_test_status || '';
    const winner = meta._headline_test_winner || '';

    const variantB = variants.find( ( v ) => v.id === 'b' )?.text || '';
    const variantC = variants.find( ( v ) => v.id === 'c' )?.text || '';

    function updateVariants( bText, cText ) {
        const updated = [ { id: 'a', text: title } ];
        if ( bText ) {
            updated.push( { id: 'b', text: bText } );
        }
        if ( cText ) {
            updated.push( { id: 'c', text: cText } );
        }
        setMeta( { ...meta, _headline_variants: JSON.stringify( updated ) } );
    }

    function toggleTest() {
        const newStatus = status === 'active' ? 'paused' : 'active';
        // Ensure variant A reflects current title on activation.
        if ( newStatus === 'active' ) {
            updateVariants( variantB, variantC );
        }
        setMeta( { ...meta, _headline_test_status: newStatus } );
    }

    const isComplete = status === 'completed';

    return (
        <PluginDocumentSettingPanel
            name="bdn-headline-test"
            title={ __( 'Headline Test', 'bdn-headline-test' ) }
        >
            <TextControl
                label={ __( 'Variant A (current title)', 'bdn-headline-test' ) }
                value={ title }
                disabled
            />
            <TextControl
                label={ __( 'Variant B', 'bdn-headline-test' ) }
                value={ variantB }
                onChange={ ( val ) => updateVariants( val, variantC ) }
                disabled={ isComplete }
            />
            <TextControl
                label={ __( 'Variant C (optional)', 'bdn-headline-test' ) }
                value={ variantC }
                onChange={ ( val ) => updateVariants( variantB, val ) }
                disabled={ isComplete }
            />
            { ! isComplete && variantB && (
                <ToggleControl
                    label={
                        status === 'active'
                            ? __( 'Test running', 'bdn-headline-test' )
                            : __( 'Start test', 'bdn-headline-test' )
                    }
                    checked={ status === 'active' }
                    onChange={ toggleTest }
                />
            ) }
            { isComplete && (
                <Notice status="success" isDismissible={ false }>
                    { __( 'Winner: Variant ', 'bdn-headline-test' ) +
                        winner.toUpperCase() }
                </Notice>
            ) }
        </PluginDocumentSettingPanel>
    );
}

registerPlugin( 'bdn-headline-test', {
    render: HeadlineTestPanel,
} );
```

**Step 2: Build to verify no JS errors**

Run: `cd cms-project/bdn-headline-test && npm install && npm run build`
Expected: Build succeeds, outputs `build/editor/index.js` and `build/frontend/index.js`

**Step 3: Enqueue editor script — update main plugin file**

Add to the `plugins_loaded` callback in `bdn-headline-test.php`:

```php
add_action( 'enqueue_block_editor_assets', function (): void {
    $asset_file = BDN_HT_DIR . 'build/editor/index.asset.php';
    $asset      = file_exists( $asset_file ) ? require $asset_file : [
        'dependencies' => [],
        'version'      => '1.0.0',
    ];
    wp_enqueue_script(
        'bdn-headline-test-editor',
        BDN_HT_URL . 'build/editor/index.js',
        $asset['dependencies'],
        $asset['version'],
        true
    );
} );
```

**Step 4: Commit**

```bash
git add cms-project/bdn-headline-test/src/editor/ cms-project/bdn-headline-test/bdn-headline-test.php
git commit -m "feat(headline-test): Gutenberg sidebar panel for managing headline variants"
```

---

### Task 7: Admin Page — Test Dashboard

**Files:**
- Modify: `cms-project/bdn-headline-test/includes/class-settings.php` (replace placeholder `render_page`)
- Create: `cms-project/bdn-headline-test/includes/class-admin-page.php`
- Create: `cms-project/bdn-headline-test/tests/test-admin-page.php`

**Step 1: Write the failing test**

```php
<?php

class Test_Admin_Page extends WP_UnitTestCase {

    public function test_query_finds_active_tests(): void {
        $p1 = self::factory()->post->create();
        $p2 = self::factory()->post->create();

        update_post_meta( $p1, '_headline_test_status', 'active' );
        update_post_meta( $p2, '_headline_test_status', 'completed' );

        $page  = new BDN_Headline_Test\Admin_Page();
        $posts = $page->get_test_posts( 'active' );

        $this->assertCount( 1, $posts );
        $this->assertEquals( $p1, $posts[0]->ID );
    }

    public function test_query_finds_all_tests(): void {
        $p1 = self::factory()->post->create();
        $p2 = self::factory()->post->create();

        update_post_meta( $p1, '_headline_test_status', 'active' );
        update_post_meta( $p2, '_headline_test_status', 'completed' );

        $page  = new BDN_Headline_Test\Admin_Page();
        $posts = $page->get_test_posts();

        $this->assertCount( 2, $posts );
    }
}
```

**Step 2: Run test to verify it fails**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Admin_Page`
Expected: FAIL — class not found

**Step 3: Write implementation**

```php
<?php

namespace BDN_Headline_Test;

class Admin_Page {

    public function register(): void {
        add_action( 'admin_menu', [ $this, 'add_menu' ] );
    }

    public function add_menu(): void {
        add_submenu_page(
            'tools.php',
            'Headline Tests',
            'Headline Tests',
            'edit_posts',
            'bdn-headline-tests',
            [ $this, 'render' ],
        );
    }

    public function get_test_posts( string $status = '' ): array {
        $meta_query = [];
        if ( $status ) {
            $meta_query[] = [
                'key'   => '_headline_test_status',
                'value' => $status,
            ];
        } else {
            $meta_query[] = [
                'key'     => '_headline_test_status',
                'value'   => '',
                'compare' => '!=',
            ];
        }

        $query = new \WP_Query( [
            'post_type'      => 'post',
            'posts_per_page' => 50,
            'meta_query'     => $meta_query,
            'orderby'        => 'modified',
            'order'          => 'DESC',
        ] );

        return $query->posts;
    }

    public function render(): void {
        $posts = $this->get_test_posts();
        ?>
        <div class="wrap">
            <h1>Headline A/B Tests</h1>
            <table class="widefat striped">
                <thead>
                    <tr>
                        <th>Post</th>
                        <th>Variants</th>
                        <th>Status</th>
                        <th>Winner</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if ( empty( $posts ) ) : ?>
                        <tr><td colspan="5">No headline tests found.</td></tr>
                    <?php endif; ?>
                    <?php foreach ( $posts as $post ) :
                        $variants = json_decode( get_post_meta( $post->ID, '_headline_variants', true ), true ) ?: [];
                        $status   = get_post_meta( $post->ID, '_headline_test_status', true );
                        $winner   = get_post_meta( $post->ID, '_headline_test_winner', true );
                    ?>
                        <tr>
                            <td><a href="<?php echo get_edit_post_link( $post->ID ); ?>"><?php echo esc_html( $post->post_title ); ?></a></td>
                            <td>
                                <?php foreach ( $variants as $v ) : ?>
                                    <div><strong><?php echo strtoupper( esc_html( $v['id'] ) ); ?>:</strong> <?php echo esc_html( $v['text'] ); ?></div>
                                <?php endforeach; ?>
                            </td>
                            <td><?php echo esc_html( ucfirst( $status ) ); ?></td>
                            <td><?php echo $winner ? strtoupper( esc_html( $winner ) ) : '—'; ?></td>
                            <td>
                                <?php if ( 'active' === $status ) : ?>
                                    <a href="<?php echo get_edit_post_link( $post->ID ); ?>">Manage</a>
                                <?php endif; ?>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
        <?php
    }
}
```

**Step 4: Remove the placeholder render_page from Settings class**

In `class-settings.php`, remove the `add_menu` and `render_page` methods (the Admin_Page class now owns the menu).

**Step 5: Run test to verify it passes**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Admin_Page`
Expected: PASS

**Step 6: Commit**

```bash
git add cms-project/bdn-headline-test/includes/class-admin-page.php cms-project/bdn-headline-test/tests/test-admin-page.php cms-project/bdn-headline-test/includes/class-settings.php
git commit -m "feat(headline-test): admin dashboard listing all active and completed tests"
```

---

### Task 8: GA4 Data API Client

**Files:**
- Create: `cms-project/bdn-headline-test/includes/class-ga4-client.php`
- Create: `cms-project/bdn-headline-test/tests/test-ga4-client.php`

**Step 1: Write the failing test**

```php
<?php

class Test_GA4_Client extends WP_UnitTestCase {

    public function test_parse_report_rows(): void {
        // Simulate the structure returned by GA4 Data API.
        $rows = [
            [ 'post_id' => '123', 'variant_id' => 'a', 'event_name' => 'headline_test_impression', 'count' => 500 ],
            [ 'post_id' => '123', 'variant_id' => 'a', 'event_name' => 'headline_test_click', 'count' => 50 ],
            [ 'post_id' => '123', 'variant_id' => 'b', 'event_name' => 'headline_test_impression', 'count' => 480 ],
            [ 'post_id' => '123', 'variant_id' => 'b', 'event_name' => 'headline_test_click', 'count' => 72 ],
        ];

        $client = new BDN_Headline_Test\GA4_Client( '', '' );
        $stats  = $client->parse_rows( $rows );

        $this->assertSame( 500, $stats[123]['a']['impressions'] );
        $this->assertSame( 50, $stats[123]['a']['clicks'] );
        $this->assertSame( 480, $stats[123]['b']['impressions'] );
        $this->assertSame( 72, $stats[123]['b']['clicks'] );
    }

    public function test_chi_squared_significant(): void {
        $client = new BDN_Headline_Test\GA4_Client( '', '' );

        // Large difference, clearly significant.
        $result = $client->is_significant(
            [ 'impressions' => 1000, 'clicks' => 100 ],
            [ 'impressions' => 1000, 'clicks' => 150 ]
        );
        $this->assertTrue( $result );
    }

    public function test_chi_squared_not_significant(): void {
        $client = new BDN_Headline_Test\GA4_Client( '', '' );

        // Nearly identical, not significant.
        $result = $client->is_significant(
            [ 'impressions' => 1000, 'clicks' => 100 ],
            [ 'impressions' => 1000, 'clicks' => 102 ]
        );
        $this->assertFalse( $result );
    }
}
```

**Step 2: Run test to verify it fails**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_GA4_Client`
Expected: FAIL — class not found

**Step 3: Write implementation**

```php
<?php

namespace BDN_Headline_Test;

class GA4_Client {

    private string $property_id;
    private string $credentials_json;

    public function __construct( string $property_id, string $credentials_json ) {
        $this->property_id      = $property_id;
        $this->credentials_json = $credentials_json;
    }

    /**
     * Fetch headline test stats from GA4 for the given post IDs.
     * Returns parsed stats array or WP_Error on failure.
     */
    public function fetch_stats( array $post_ids ): array|\WP_Error {
        if ( empty( $this->property_id ) || empty( $this->credentials_json ) ) {
            return new \WP_Error( 'ga4_not_configured', 'GA4 credentials not configured.' );
        }

        try {
            $client = new \Google\Analytics\Data\V1beta\BetaAnalyticsDataClient( [
                'credentials' => json_decode( $this->credentials_json, true ),
            ] );

            $response = $client->runReport( [
                'property'   => 'properties/' . $this->property_id,
                'dateRanges' => [
                    [ 'startDate' => '7daysAgo', 'endDate' => 'today' ],
                ],
                'dimensions' => [
                    [ 'name' => 'customEvent:post_id' ],
                    [ 'name' => 'customEvent:variant_id' ],
                    [ 'name' => 'eventName' ],
                ],
                'metrics' => [
                    [ 'name' => 'eventCount' ],
                ],
                'dimensionFilter' => [
                    'andGroup' => [
                        'expressions' => [
                            [
                                'filter' => [
                                    'fieldName'    => 'eventName',
                                    'inListFilter' => [
                                        'values' => [
                                            'headline_test_impression',
                                            'headline_test_click',
                                        ],
                                    ],
                                ],
                            ],
                        ],
                    ],
                ],
            ] );

            $rows = [];
            foreach ( $response->getRows() as $row ) {
                $dims = $row->getDimensionValues();
                $rows[] = [
                    'post_id'    => $dims[0]->getValue(),
                    'variant_id' => $dims[1]->getValue(),
                    'event_name' => $dims[2]->getValue(),
                    'count'      => (int) $row->getMetricValues()[0]->getValue(),
                ];
            }

            return $this->parse_rows( $rows );
        } catch ( \Throwable $e ) {
            return new \WP_Error( 'ga4_api_error', $e->getMessage() );
        }
    }

    /**
     * Parse raw GA4 rows into structured stats.
     * Returns: [ post_id => [ variant_id => [ 'impressions' => int, 'clicks' => int ] ] ]
     */
    public function parse_rows( array $rows ): array {
        $stats = [];
        foreach ( $rows as $row ) {
            $pid = (int) $row['post_id'];
            $vid = $row['variant_id'];
            if ( ! isset( $stats[ $pid ][ $vid ] ) ) {
                $stats[ $pid ][ $vid ] = [ 'impressions' => 0, 'clicks' => 0 ];
            }
            if ( str_contains( $row['event_name'], 'impression' ) ) {
                $stats[ $pid ][ $vid ]['impressions'] = $row['count'];
            } else {
                $stats[ $pid ][ $vid ]['clicks'] = $row['count'];
            }
        }
        return $stats;
    }

    /**
     * Chi-squared test for two variants. Returns true if difference is significant (p < 0.05).
     */
    public function is_significant( array $a, array $b ): bool {
        $a_clicks     = $a['clicks'];
        $a_no_clicks  = $a['impressions'] - $a['clicks'];
        $b_clicks     = $b['clicks'];
        $b_no_clicks  = $b['impressions'] - $b['clicks'];
        $total        = $a['impressions'] + $b['impressions'];
        $total_clicks = $a_clicks + $b_clicks;
        $total_no     = $a_no_clicks + $b_no_clicks;

        if ( $total === 0 || $total_clicks === 0 || $total_no === 0 ) {
            return false;
        }

        // Expected values.
        $ea_click = ( $a['impressions'] * $total_clicks ) / $total;
        $ea_no    = ( $a['impressions'] * $total_no ) / $total;
        $eb_click = ( $b['impressions'] * $total_clicks ) / $total;
        $eb_no    = ( $b['impressions'] * $total_no ) / $total;

        $chi2 = ( ( $a_clicks - $ea_click ) ** 2 ) / $ea_click
              + ( ( $a_no_clicks - $ea_no ) ** 2 ) / $ea_no
              + ( ( $b_clicks - $eb_click ) ** 2 ) / $eb_click
              + ( ( $b_no_clicks - $eb_no ) ** 2 ) / $eb_no;

        // 3.841 is the chi-squared critical value for df=1, p=0.05.
        return $chi2 >= 3.841;
    }
}
```

**Step 4: Run test to verify it passes**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_GA4_Client`
Expected: PASS

**Step 5: Commit**

```bash
git add cms-project/bdn-headline-test/includes/class-ga4-client.php cms-project/bdn-headline-test/tests/test-ga4-client.php
git commit -m "feat(headline-test): GA4 Data API client with chi-squared significance test"
```

---

### Task 9: Cron Resolver

**Files:**
- Create: `cms-project/bdn-headline-test/includes/class-cron-resolver.php`
- Create: `cms-project/bdn-headline-test/tests/test-cron-resolver.php`

**Step 1: Write the failing test**

```php
<?php

class Test_Cron_Resolver extends WP_UnitTestCase {

    public function test_declares_winner_and_updates_title(): void {
        $post_id = self::factory()->post->create( [ 'post_title' => 'Original' ] );
        $variants = wp_json_encode( [
            [ 'id' => 'a', 'text' => 'Original' ],
            [ 'id' => 'b', 'text' => 'Better Headline' ],
        ] );
        update_post_meta( $post_id, '_headline_variants', $variants );
        update_post_meta( $post_id, '_headline_test_status', 'active' );

        $resolver = new BDN_Headline_Test\Cron_Resolver(
            new BDN_Headline_Test\Settings()
        );

        // Simulate stats where variant B wins.
        $stats = [
            $post_id => [
                'a' => [ 'impressions' => 1000, 'clicks' => 50 ],
                'b' => [ 'impressions' => 1000, 'clicks' => 100 ],
            ],
        ];

        $resolver->evaluate_test( $post_id, $stats[ $post_id ] );

        $this->assertSame( 'completed', get_post_meta( $post_id, '_headline_test_status', true ) );
        $this->assertSame( 'b', get_post_meta( $post_id, '_headline_test_winner', true ) );
        $this->assertSame( 'Better Headline', get_the_title( $post_id ) );
    }

    public function test_does_not_resolve_below_min_impressions(): void {
        $post_id = self::factory()->post->create( [ 'post_title' => 'Original' ] );
        $variants = wp_json_encode( [
            [ 'id' => 'a', 'text' => 'Original' ],
            [ 'id' => 'b', 'text' => 'Alt' ],
        ] );
        update_post_meta( $post_id, '_headline_variants', $variants );
        update_post_meta( $post_id, '_headline_test_status', 'active' );

        $resolver = new BDN_Headline_Test\Cron_Resolver(
            new BDN_Headline_Test\Settings()
        );

        $stats = [
            'a' => [ 'impressions' => 50, 'clicks' => 5 ],
            'b' => [ 'impressions' => 50, 'clicks' => 10 ],
        ];

        $resolver->evaluate_test( $post_id, $stats );

        $this->assertSame( 'active', get_post_meta( $post_id, '_headline_test_status', true ) );
    }
}
```

**Step 2: Run test to verify it fails**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Cron_Resolver`
Expected: FAIL — class not found

**Step 3: Write implementation**

```php
<?php

namespace BDN_Headline_Test;

class Cron_Resolver {

    private Settings $settings;

    public function __construct( Settings $settings ) {
        $this->settings = $settings;
    }

    public function register(): void {
        add_action( 'bdn_ht_resolve_tests', [ $this, 'run' ] );

        if ( ! wp_next_scheduled( 'bdn_ht_resolve_tests' ) ) {
            wp_schedule_event( time(), 'hourly', 'bdn_ht_resolve_tests' );
        }
    }

    public function run(): void {
        $ga4 = new GA4_Client(
            $this->settings->get( 'ga4_property_id' ),
            $this->settings->get( 'ga4_credentials_json' )
        );

        $active_posts = get_posts( [
            'post_type'      => 'post',
            'posts_per_page' => -1,
            'meta_key'       => '_headline_test_status',
            'meta_value'     => 'active',
            'fields'         => 'ids',
        ] );

        if ( empty( $active_posts ) ) {
            return;
        }

        $all_stats = $ga4->fetch_stats( $active_posts );
        if ( is_wp_error( $all_stats ) ) {
            return; // Retry next hour.
        }

        foreach ( $active_posts as $post_id ) {
            if ( isset( $all_stats[ $post_id ] ) ) {
                $this->evaluate_test( $post_id, $all_stats[ $post_id ] );
            }
        }
    }

    /**
     * Evaluate a single test's stats and resolve if ready.
     *
     * @param int   $post_id Post ID.
     * @param array $stats   [ variant_id => [ 'impressions' => int, 'clicks' => int ] ]
     */
    public function evaluate_test( int $post_id, array $stats ): void {
        $min_impressions = $this->settings->get( 'min_impressions' );

        // Check all variants have enough impressions.
        foreach ( $stats as $variant_stats ) {
            if ( $variant_stats['impressions'] < $min_impressions ) {
                return; // Not enough data yet.
            }
        }

        $variant_ids = array_keys( $stats );
        $ga4_client  = new GA4_Client( '', '' ); // Only using static methods.

        // Find the variant with the highest CTR.
        $best_id  = $variant_ids[0];
        $best_ctr = $stats[ $best_id ]['clicks'] / max( 1, $stats[ $best_id ]['impressions'] );

        foreach ( $variant_ids as $vid ) {
            $ctr = $stats[ $vid ]['clicks'] / max( 1, $stats[ $vid ]['impressions'] );
            if ( $ctr > $best_ctr ) {
                $best_id  = $vid;
                $best_ctr = $ctr;
            }
        }

        // Check significance against each other variant.
        $significant = true;
        foreach ( $variant_ids as $vid ) {
            if ( $vid === $best_id ) {
                continue;
            }
            if ( ! $ga4_client->is_significant( $stats[ $best_id ], $stats[ $vid ] ) ) {
                $significant = false;
                break;
            }
        }

        if ( ! $significant ) {
            // TODO: Check max duration and force-resolve if expired.
            return;
        }

        $this->declare_winner( $post_id, $best_id );
    }

    private function declare_winner( int $post_id, string $winner_id ): void {
        update_post_meta( $post_id, '_headline_test_status', 'completed' );
        update_post_meta( $post_id, '_headline_test_winner', $winner_id );

        // Update post title to the winning variant text.
        $variants = json_decode(
            get_post_meta( $post_id, '_headline_variants', true ),
            true
        ) ?: [];

        foreach ( $variants as $v ) {
            if ( $v['id'] === $winner_id ) {
                wp_update_post( [
                    'ID'         => $post_id,
                    'post_title' => $v['text'],
                ] );
                break;
            }
        }
    }
}
```

**Step 4: Run test to verify it passes**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit --filter Test_Cron_Resolver`
Expected: PASS

**Step 5: Commit**

```bash
git add cms-project/bdn-headline-test/includes/class-cron-resolver.php cms-project/bdn-headline-test/tests/test-cron-resolver.php
git commit -m "feat(headline-test): cron resolver evaluates tests and declares winners"
```

---

### Task 10: Settings Page UI

**Files:**
- Modify: `cms-project/bdn-headline-test/includes/class-settings.php`

**Step 1: Add settings page rendering with fields**

Update `render_page` in `class-settings.php` to output a form with fields for:
- GA4 Property ID (text input)
- GA4 Service Account JSON (textarea)
- Minimum impressions per variant (number input, default 1000)
- Maximum test duration hours (number input, default 72)

Use standard `settings_fields()` / `do_settings_sections()` WordPress pattern.

**Step 2: Verify settings save by visiting the page in browser**

Manual test: Navigate to Tools > Headline Tests Settings, enter values, save, confirm they persist.

**Step 3: Commit**

```bash
git add cms-project/bdn-headline-test/includes/class-settings.php
git commit -m "feat(headline-test): settings page UI for GA4 credentials and test thresholds"
```

---

### Task 11: Integration Test & Cleanup

**Files:**
- Create: `cms-project/bdn-headline-test/tests/test-integration.php`

**Step 1: Write end-to-end test**

```php
<?php

class Test_Integration extends WP_UnitTestCase {

    public function set_up(): void {
        parent::set_up();
        ( new BDN_Headline_Test\Post_Meta() )->register();
        do_action( 'init' );
        ( new BDN_Headline_Test\Title_Filter() )->register();
    }

    public function test_full_lifecycle(): void {
        // 1. Create a post.
        $post_id = self::factory()->post->create( [ 'post_title' => 'Original Headline' ] );

        // 2. Set up a test with two variants.
        $variants = wp_json_encode( [
            [ 'id' => 'a', 'text' => 'Original Headline' ],
            [ 'id' => 'b', 'text' => 'Clickbait Headline' ],
        ] );
        update_post_meta( $post_id, '_headline_variants', $variants );
        update_post_meta( $post_id, '_headline_test_status', 'active' );

        // 3. Verify title filter injects data attributes.
        $title = apply_filters( 'the_title', 'Original Headline', $post_id );
        $this->assertStringContainsString( 'data-headline-test', $title );

        // 4. Simulate resolution — variant B wins.
        $resolver = new BDN_Headline_Test\Cron_Resolver( new BDN_Headline_Test\Settings() );
        $resolver->evaluate_test( $post_id, [
            'a' => [ 'impressions' => 2000, 'clicks' => 100 ],
            'b' => [ 'impressions' => 2000, 'clicks' => 200 ],
        ] );

        // 5. Verify winner declared and title updated.
        $this->assertSame( 'completed', get_post_meta( $post_id, '_headline_test_status', true ) );
        $this->assertSame( 'b', get_post_meta( $post_id, '_headline_test_winner', true ) );
        $this->assertSame( 'Clickbait Headline', get_the_title( $post_id ) );

        // 6. Verify title filter no longer injects attributes.
        $title = apply_filters( 'the_title', 'Clickbait Headline', $post_id );
        $this->assertStringNotContainsString( 'data-headline-test', $title );
    }
}
```

**Step 2: Run full test suite**

Run: `cd cms-project/bdn-headline-test && vendor/bin/phpunit`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add cms-project/bdn-headline-test/tests/test-integration.php
git commit -m "test(headline-test): integration test covering full test lifecycle"
```

---

### Task 12: README

**Files:**
- Create: `cms-project/bdn-headline-test/README.md`

**Step 1: Write README covering:**
- What the plugin does
- Installation (composer install, npm install, npm run build, activate plugin)
- Configuration (GA4 setup steps)
- Usage (how editors create tests)
- How auto-resolution works

**Step 2: Commit**

```bash
git add cms-project/bdn-headline-test/README.md
git commit -m "docs(headline-test): README with setup and usage instructions"
```

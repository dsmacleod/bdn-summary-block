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

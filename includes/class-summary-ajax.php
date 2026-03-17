<?php
namespace BDN_Summary;

class Summary_Ajax {

    public function __construct(
        private Summary_Settings $settings,
    ) {}

    public function register(): void {
        add_action( 'wp_ajax_bdn_generate_summary', [ $this, 'handle' ] );
        add_action( 'enqueue_block_editor_assets',  [ $this, 'localize_block_data' ] );
    }

    /**
     * Pass AJAX URL, nonce, and AI policy URL to the block's editor script.
     */
    public function localize_block_data(): void {
        $handle = generate_block_asset_handle( 'bdn/story-summary', 'editorScript' );
        wp_add_inline_script(
            $handle,
            'window.bdnSummaryData = ' . wp_json_encode( [
                'ajaxUrl'     => admin_url( 'admin-ajax.php' ),
                'nonce'       => wp_create_nonce( 'bdn_generate_summary' ),
                'aiPolicyUrl' => $this->settings->get_ai_policy_url(),
            ] ) . ';',
            'before'
        );
    }

    /**
     * Handle the wp_ajax_bdn_generate_summary AJAX request.
     * Expects POST: nonce, post_id
     */
    public function handle(): void {
        error_log( '[bdn-summary] handle() called' );
        check_ajax_referer( 'bdn_generate_summary', 'nonce' );

        $post_id = (int) ( $_POST['post_id'] ?? 0 );
        if ( ! $post_id ) {
            error_log( '[bdn-summary] Missing post_id' );
            wp_send_json_error( 'Missing post_id', 400 );
        }

        if ( ! current_user_can( 'edit_post', $post_id ) ) {
            error_log( '[bdn-summary] Unauthorized for post ' . $post_id );
            wp_send_json_error( 'Unauthorized', 403 );
        }

        $post = get_post( $post_id );
        if ( ! $post ) {
            error_log( '[bdn-summary] Post not found: ' . $post_id );
            wp_send_json_error( 'Post not found', 404 );
        }

        error_log( '[bdn-summary] Calling generate_bullets for post ' . $post_id );
        $bullets = $this->generate_bullets( $post );
        if ( $bullets === null ) {
            wp_send_json_error( 'Failed to generate summary. Try again.', 500 );
        }

        wp_send_json_success( [ 'bullets' => $bullets ] );
    }

    /**
     * Call Nota's key-points endpoint and return an array of bullet strings.
     *
     * @return string[]|null Bullet strings, or null on any failure.
     */
    public function generate_bullets( \WP_Post $post ): ?array {
        $nota_url = (string) get_option( 'nota_api_url', '' );
        $nota_key = (string) get_option( 'nota_api_key', '' );

        if ( ! $nota_url || ! $nota_key ) {
            error_log( '[bdn-summary] Nota API credentials not configured.' );
            return null;
        }

        // Strip HTML and normalize whitespace; cap at 60,000 chars (Nota limit).
        $text = wp_strip_all_tags( $post->post_content );
        $text = html_entity_decode( $text, ENT_QUOTES | ENT_HTML5, 'UTF-8' );
        $text = (string) preg_replace( '/\s+/', ' ', trim( $text ) );
        $text = mb_substr( $text, 0, 60000 );

        $response = wp_remote_post(
            trailingslashit( $nota_url ) . 'wordpress/v1/sum/key-points',
            [
                'headers' => [
                    'nota-subscription-key' => $nota_key,
                    'Content-Type'          => 'application/json',
                ],
                'body'    => wp_json_encode( [
                    'text'               => $text,
                    'contentInputSource' => [
                        'type'        => 'cms',
                        'cmsRecordId' => $post->ID,
                        'cmsProvider' => 'WordPress/' . get_bloginfo( 'version' ),
                        'cmsName'     => get_bloginfo( 'url' ),
                    ],
                ] ),
                'timeout' => 30,
            ]
        );

        if ( is_wp_error( $response ) ) {
            error_log( '[bdn-summary] Nota request failed: ' . $response->get_error_message() );
            return null;
        }

        $status = wp_remote_retrieve_response_code( $response );
        if ( $status < 200 || $status >= 300 ) {
            error_log( "[bdn-summary] Nota returned HTTP {$status}" );
            return null;
        }

        $body = json_decode( wp_remote_retrieve_body( $response ), true );
        if ( ! is_array( $body ) ) {
            error_log( '[bdn-summary] Nota returned invalid JSON' );
            return null;
        }

        error_log( '[bdn-summary] Nota response body: ' . wp_json_encode( $body ) );

        $bullets = $this->parse_bullets( $body );
        if ( empty( $bullets ) ) {
            error_log( '[bdn-summary] No bullets in Nota response. Keys: ' . implode( ', ', array_keys( $body ) ) );
            return null;
        }

        return array_slice( $bullets, 0, 6 );
    }

    /**
     * Extract bullet strings from the Nota API response.
     * Handles both { "keyPoints": [...] } and { "data": [...] } response shapes.
     *
     * @param array<string,mixed> $body Decoded JSON response
     * @return string[]
     */
    private function parse_bullets( array $body ): array {
        $candidates = $body['result']['keyPoints'] ?? $body['keyPoints'] ?? $body['data'] ?? $body['key_points'] ?? [];

        if ( ! is_array( $candidates ) ) {
            return [];
        }

        return array_values(
            array_filter(
                array_map(
                    fn( mixed $item ) => is_string( $item )
                        ? trim( $item )
                        : ( is_array( $item ) ? trim( (string) ( $item['text'] ?? '' ) ) : '' ),
                    $candidates
                ),
                fn( string $s ) => $s !== ''
            )
        );
    }
}

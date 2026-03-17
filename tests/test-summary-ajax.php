<?php
use BDN_Summary\Summary_Ajax;
use BDN_Summary\Summary_Settings;

class Test_Summary_Ajax extends WP_UnitTestCase {

    private Summary_Ajax $ajax;

    public function set_up(): void {
        parent::set_up();
        update_option( 'nota_api_url', 'https://api.nota.ai/' );
        update_option( 'nota_api_key', 'test-key-abc' );
        $this->ajax = new Summary_Ajax( new Summary_Settings() );
    }

    public function tear_down(): void {
        remove_all_filters( 'pre_http_request' );
        delete_option( 'nota_api_url' );
        delete_option( 'nota_api_key' );
        parent::tear_down();
    }

    public function test_returns_null_when_nota_api_key_missing(): void {
        delete_option( 'nota_api_key' );
        $post = $this->factory->post->create_and_get( [ 'post_content' => 'Some content.' ] );
        $this->assertNull( $this->ajax->generate_bullets( $post ) );
    }

    public function test_returns_null_when_nota_api_url_missing(): void {
        delete_option( 'nota_api_url' );
        $post = $this->factory->post->create_and_get( [ 'post_content' => 'Some content.' ] );
        $this->assertNull( $this->ajax->generate_bullets( $post ) );
    }

    public function test_returns_bullets_from_key_points_response(): void {
        add_filter( 'pre_http_request', function () {
            return [
                'body'     => json_encode( [ 'keyPoints' => [ 'Bullet one.', 'Bullet two.', 'Bullet three.' ] ] ),
                'response' => [ 'code' => 200 ],
                'headers'  => [],
            ];
        } );

        $post   = $this->factory->post->create_and_get( [ 'post_content' => 'Story content here.' ] );
        $result = $this->ajax->generate_bullets( $post );

        $this->assertIsArray( $result );
        $this->assertCount( 3, $result );
        $this->assertSame( 'Bullet one.', $result[0] );
    }

    public function test_returns_null_on_wp_error(): void {
        add_filter( 'pre_http_request', function () {
            return new WP_Error( 'http_request_failed', 'Connection timed out' );
        } );

        $post = $this->factory->post->create_and_get( [ 'post_content' => 'Content.' ] );
        $this->assertNull( $this->ajax->generate_bullets( $post ) );
    }

    public function test_returns_null_on_non_200_response(): void {
        add_filter( 'pre_http_request', function () {
            return [
                'body'     => json_encode( [ 'error' => 'Service unavailable' ] ),
                'response' => [ 'code' => 503 ],
                'headers'  => [],
            ];
        } );

        $post = $this->factory->post->create_and_get( [ 'post_content' => 'Content.' ] );
        $this->assertNull( $this->ajax->generate_bullets( $post ) );
    }

    public function test_caps_bullets_at_six(): void {
        add_filter( 'pre_http_request', function () {
            return [
                'body'     => json_encode( [
                    'keyPoints' => [ 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H' ],
                ] ),
                'response' => [ 'code' => 200 ],
                'headers'  => [],
            ];
        } );

        $post   = $this->factory->post->create_and_get( [ 'post_content' => 'Content.' ] );
        $result = $this->ajax->generate_bullets( $post );
        $this->assertCount( 6, $result );
    }

    public function test_handles_data_key_as_fallback(): void {
        add_filter( 'pre_http_request', function () {
            return [
                'body'     => json_encode( [ 'data' => [ 'Bullet A.', 'Bullet B.' ] ] ),
                'response' => [ 'code' => 200 ],
                'headers'  => [],
            ];
        } );

        $post   = $this->factory->post->create_and_get( [ 'post_content' => 'Content.' ] );
        $result = $this->ajax->generate_bullets( $post );
        $this->assertCount( 2, $result );
        $this->assertSame( 'Bullet A.', $result[0] );
    }

    public function test_handles_key_points_snake_case_as_fallback(): void {
        add_filter( 'pre_http_request', function () {
            return [
                'body'     => json_encode( [ 'key_points' => [ 'Snake one.', 'Snake two.' ] ] ),
                'response' => [ 'code' => 200 ],
                'headers'  => [],
            ];
        } );

        $post   = $this->factory->post->create_and_get( [ 'post_content' => 'Content.' ] );
        $result = $this->ajax->generate_bullets( $post );
        $this->assertIsArray( $result );
        $this->assertCount( 2, $result );
        $this->assertSame( 'Snake one.', $result[0] );
    }

    public function test_handles_object_shaped_bullets(): void {
        add_filter( 'pre_http_request', function () {
            return [
                'body'     => json_encode( [
                    'keyPoints' => [
                        [ 'text' => 'Object bullet one.' ],
                        [ 'text' => 'Object bullet two.' ],
                    ],
                ] ),
                'response' => [ 'code' => 200 ],
                'headers'  => [],
            ];
        } );

        $post   = $this->factory->post->create_and_get( [ 'post_content' => 'Content.' ] );
        $result = $this->ajax->generate_bullets( $post );
        $this->assertIsArray( $result );
        $this->assertCount( 2, $result );
        $this->assertSame( 'Object bullet one.', $result[0] );
    }
}

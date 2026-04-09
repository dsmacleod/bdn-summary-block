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

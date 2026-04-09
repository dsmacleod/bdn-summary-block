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

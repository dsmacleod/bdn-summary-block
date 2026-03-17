<?php
/**
 * Server-side render for bdn/story-summary block.
 *
 * @var array  $attributes Block attributes: bullets (string[]), generated (bool)
 * @var string $content    Inner block content (unused — no inner blocks)
 */

$bullets   = $attributes['bullets']   ?? [];
$generated = $attributes['generated'] ?? false;

if ( ! $generated || empty( $bullets ) ) {
    return '';
}

$ai_policy_url = get_option( 'bdn_summary_ai_policy_url', '' );

$policy_link = '';
if ( $ai_policy_url ) {
    $policy_link = sprintf(
        ' <a href="%s" rel="noopener noreferrer">%s</a>',
        esc_url( $ai_policy_url ),
        esc_html__( 'Read our AI policy.', 'bdn-summary-block' )
    );
}

$wrapper = get_block_wrapper_attributes( [ 'class' => 'bdn-summary-block' ] );
?>
<div <?php echo $wrapper; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>>
    <p class="bdn-summary-block__heading">
        <?php esc_html_e( 'In brief', 'bdn-summary-block' ); ?>
    </p>
    <ul class="bdn-summary-block__bullets">
        <?php foreach ( $bullets as $bullet ) : ?>
            <li class="bdn-summary-block__bullet">
                <?php echo esc_html( $bullet ); ?>
            </li>
        <?php endforeach; ?>
    </ul>
    <p class="bdn-summary-block__attribution">
        <?php esc_html_e( 'Generated with the help of AI and reviewed by a BDN editor.', 'bdn-summary-block' ); ?>
        <?php echo $policy_link; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
    </p>
</div>

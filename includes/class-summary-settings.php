<?php
namespace BDN_Summary;

class Summary_Settings {

    public const OPTION_AI_POLICY_URL = 'bdn_summary_ai_policy_url';

    public function register(): void {
        add_action( 'admin_menu', [ $this, 'add_page' ] );
        add_action( 'admin_init', [ $this, 'register_settings' ] );
    }

    public function add_page(): void {
        add_options_page(
            'BDN Summary Block',
            'BDN Summary Block',
            'manage_options',
            'bdn-summary-block',
            [ $this, 'render_page' ]
        );
    }

    public function register_settings(): void {
        register_setting( 'bdn_summary', self::OPTION_AI_POLICY_URL, [
            'sanitize_callback' => 'esc_url_raw',
        ] );
        register_setting( 'bdn_summary', 'nota_api_url', [
            'sanitize_callback' => 'esc_url_raw',
        ] );
        register_setting( 'bdn_summary', 'nota_api_key', [
            'sanitize_callback' => 'sanitize_text_field',
        ] );
    }

    public function get_ai_policy_url(): string {
        return (string) get_option( self::OPTION_AI_POLICY_URL, '' );
    }

    public function get_nota_url(): string {
        return (string) get_option( 'nota_api_url', '' );
    }

    public function get_nota_key(): string {
        return (string) get_option( 'nota_api_key', '' );
    }

    public function render_page(): void {
        if ( ! current_user_can( 'manage_options' ) ) {
            return;
        }
        ?>
        <div class="wrap">
            <h1>BDN Summary Block Settings</h1>
            <form method="post" action="options.php">
                <?php settings_fields( 'bdn_summary' ); ?>
                <table class="form-table">
                    <tr>
                        <th>Nota API URL</th>
                        <td>
                            <input type="url"
                                name="nota_api_url"
                                value="<?php echo esc_attr( $this->get_nota_url() ); ?>"
                                class="regular-text"
                                placeholder="https://tools.heynota.com">
                            <p class="description">
                                Base URL for the Nota summarization API.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <th>Nota API Key</th>
                        <td>
                            <input type="password"
                                name="nota_api_key"
                                value="<?php echo esc_attr( $this->get_nota_key() ); ?>"
                                class="regular-text"
                                autocomplete="off">
                            <p class="description">
                                Your Nota subscription key (primary or secondary).
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <th>AI Policy URL</th>
                        <td>
                            <input type="url"
                                name="<?php echo esc_attr( self::OPTION_AI_POLICY_URL ); ?>"
                                value="<?php echo esc_attr( $this->get_ai_policy_url() ); ?>"
                                class="regular-text"
                                placeholder="https://bangordailynews.com/ai-policy/">
                            <p class="description">
                                URL for the "Read our AI policy" link shown in every story summary block.
                            </p>
                        </td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
        </div>
        <?php
    }
}

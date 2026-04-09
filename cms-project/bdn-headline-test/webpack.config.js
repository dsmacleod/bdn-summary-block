const defaultConfig = require( '@wordpress/scripts/config/webpack.config' );
const path = require( 'path' );

module.exports = {
    ...defaultConfig,
    entry: {
        'frontend/index': path.resolve( __dirname, 'src/frontend/index.js' ),
        'editor/index': path.resolve( __dirname, 'src/editor/index.js' ),
    },
};

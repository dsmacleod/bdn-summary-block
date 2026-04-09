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

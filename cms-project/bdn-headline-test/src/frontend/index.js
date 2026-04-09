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

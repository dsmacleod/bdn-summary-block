<?php

namespace BDN_Headline_Test;

class GA4_Client {

    private string $property_id;
    private string $credentials_json;

    public function __construct( string $property_id, string $credentials_json ) {
        $this->property_id      = $property_id;
        $this->credentials_json = $credentials_json;
    }

    public function fetch_stats( array $post_ids ): array|\WP_Error {
        if ( empty( $this->property_id ) || empty( $this->credentials_json ) ) {
            return new \WP_Error( 'ga4_not_configured', 'GA4 credentials not configured.' );
        }

        try {
            $client = new \Google\Analytics\Data\V1beta\BetaAnalyticsDataClient( [
                'credentials' => json_decode( $this->credentials_json, true ),
            ] );

            $response = $client->runReport( [
                'property'   => 'properties/' . $this->property_id,
                'dateRanges' => [
                    [ 'startDate' => '7daysAgo', 'endDate' => 'today' ],
                ],
                'dimensions' => [
                    [ 'name' => 'customEvent:post_id' ],
                    [ 'name' => 'customEvent:variant_id' ],
                    [ 'name' => 'eventName' ],
                ],
                'metrics' => [
                    [ 'name' => 'eventCount' ],
                ],
                'dimensionFilter' => [
                    'andGroup' => [
                        'expressions' => [
                            [
                                'filter' => [
                                    'fieldName'    => 'eventName',
                                    'inListFilter' => [
                                        'values' => [
                                            'headline_test_impression',
                                            'headline_test_click',
                                        ],
                                    ],
                                ],
                            ],
                            [
                                'filter' => [
                                    'fieldName'    => 'customEvent:post_id',
                                    'inListFilter' => [
                                        'values' => array_map( 'strval', $post_ids ),
                                    ],
                                ],
                            ],
                        ],
                    ],
                ],
            ] );

            $rows = [];
            foreach ( $response->getRows() as $row ) {
                $dims = $row->getDimensionValues();
                $rows[] = [
                    'post_id'    => $dims[0]->getValue(),
                    'variant_id' => $dims[1]->getValue(),
                    'event_name' => $dims[2]->getValue(),
                    'count'      => (int) $row->getMetricValues()[0]->getValue(),
                ];
            }

            return $this->parse_rows( $rows );
        } catch ( \Throwable $e ) {
            return new \WP_Error( 'ga4_api_error', $e->getMessage() );
        }
    }

    public function parse_rows( array $rows ): array {
        $stats = [];
        foreach ( $rows as $row ) {
            $pid = (int) $row['post_id'];
            $vid = $row['variant_id'];
            if ( ! isset( $stats[ $pid ][ $vid ] ) ) {
                $stats[ $pid ][ $vid ] = [ 'impressions' => 0, 'clicks' => 0 ];
            }
            if ( str_contains( $row['event_name'], 'impression' ) ) {
                $stats[ $pid ][ $vid ]['impressions'] = $row['count'];
            } else {
                $stats[ $pid ][ $vid ]['clicks'] = $row['count'];
            }
        }
        return $stats;
    }

    public function is_significant( array $a, array $b ): bool {
        $a_clicks     = $a['clicks'];
        $a_no_clicks  = $a['impressions'] - $a['clicks'];
        $b_clicks     = $b['clicks'];
        $b_no_clicks  = $b['impressions'] - $b['clicks'];
        $total        = $a['impressions'] + $b['impressions'];
        $total_clicks = $a_clicks + $b_clicks;
        $total_no     = $a_no_clicks + $b_no_clicks;

        if ( $total === 0 || $total_clicks === 0 || $total_no === 0 ) {
            return false;
        }

        $ea_click = ( $a['impressions'] * $total_clicks ) / $total;
        $ea_no    = ( $a['impressions'] * $total_no ) / $total;
        $eb_click = ( $b['impressions'] * $total_clicks ) / $total;
        $eb_no    = ( $b['impressions'] * $total_no ) / $total;

        $chi2 = ( ( $a_clicks - $ea_click ) ** 2 ) / $ea_click
              + ( ( $a_no_clicks - $ea_no ) ** 2 ) / $ea_no
              + ( ( $b_clicks - $eb_click ) ** 2 ) / $eb_click
              + ( ( $b_no_clicks - $eb_no ) ** 2 ) / $eb_no;

        return $chi2 >= 3.841;
    }
}

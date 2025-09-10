# AtmosInsight Implementation Questions

These questions will help complete the implementation with accurate details specific to your requirements and infrastructure.

## Domain & DNS Configuration

1. **Domain Setup**: Do you already own `westfam.media` and have it configured in Cloudflare? Should I proceed with the `weather.westfam.media` subdomain as specified?

# Yes I own this domain, and have started prep to route it to the subdomain weather.westfam.media

2. **DNS Strategy**: Would you prefer to:
   - Delegate the `weather.westfam.media` subdomain to Route53 (as specified in SPEC)
   - Keep DNS in Cloudflare and CNAME to CloudFront (alternative approach)

# See above answer. Route to Route53.

## Data Sources & Processing

3. **GOES Data Processing**: The GOES-prepare Lambda currently has placeholder logic. Do you want me to implement the full GOES ABI Band 13 processing pipeline with:
   - NetCDF4 file handling from NOAA's AWS Open Data
   - Brightness temperature extraction and scaling
   - COG conversion with proper geospatial referencing

# Yes. Implement the FULL GOES ABI Band 13 processing pipeline.

4. **NEXRAD Level II Processing**: Should I implement the full NEXRAD Level II pipeline with:
   - Py-ART for Level II file reading
   - Tilt 0 super-res reflectivity extraction
   - Polar to Cartesian gridding
   - NEXRAD color palette application

# Yes. Implement the FULL NEXRAD Level II processing pipeline.

5. **MRMS Data Access**: Do you have preferred access to MRMS data:
   - Direct from NCEP NOMADS (requires authentication)
   - Via AWS Open Data if available
   - Alternative MRMS data source

  # AWS Open Data if available. 

## Basemap & Styling

6. **PMTiles Source**: Do you have access to OpenMapTiles Planet data, or should I:
   - Provide instructions for downloading/building PMTiles
   - Use a smaller regional extract for testing
   - Suggest alternative basemap sources

  # I have access to the planet-wide OMT .mbtiles file.

7. **CyclOSM Styling**: The current CyclOSM style is basic. Do you want:
   - Full CyclOSM style conversion with all layers
   - Simplified version focused on key features
   - Custom styling preferences

# A full conversion to CyclOSM with all layers.

## Infrastructure & Deployment

8. **AWS Account Setup**: Do you have:
   - AWS CLI configured with appropriate permissions
   - ECR repository for Lambda container images
   - Preference for deployment automation (GitHub Actions, etc.)

# I don't believe CLI is installed, but I do have all the necessary credentials/permissions.
# I do not have ECR for lambda set up
# I would prefer to use GitHub Actions for deployment automation IF thats the best option.

9. **Budget & Scaling**: The SPEC mentions $30/month budget:
   - Are there specific cost monitoring preferences
   - Expected traffic patterns beyond the 5-10k requests/month estimate
   - Preference for reserved capacity vs. on-demand



## Development & Testing

10. **Local Development**: Do you want:
    - Local development setup with mock data
    - Docker Compose for local service testing  
    - Integration with live AWS services during development

    # Local Dev should not have mock data, it should either integrate with live AWS services, or replicate prod exactly.

11. **Data Processing Priority**: Which data layers should I prioritize for full implementation:
    - NWS Alerts (already functional)
    - GOES satellite imagery
    - NEXRAD single-site radar
    - MRMS national mosaic

    # We should prioritize NEXRAD, Then MRMS, Then GOES.

## Monitoring & Operations

12. **Observability Requirements**: Beyond basic CloudWatch, do you want:
    - Custom dashboards for data freshness
    - Slack/email alerting for outages
    - Public status page implementation

    # Email/Discord/Text alerting, Custom Dashboard would be cool too. 

13. **Data Retention**: The SPEC mentions 7-day COG retention:
    - Should older data be archived to cheaper storage
    - Preference for manual vs. automated cleanup

# I want to archive older data to S3 Glacier. Old data should be stored for later "Data graphing" against prior years. (historical charts for specific local areas)

Please review these questions and provide answers where you have specific preferences or requirements. I can proceed with reasonable defaults for any questions you prefer to skip.
import geopandas as gpd
import pandas as pd
import requests
from io import BytesIO
import warnings

warnings.filterwarnings('ignore', message='Geometry is in a geographic CRS.')

# Load Official Cariboo Fire Centre Boundaries
zones_wfs_url = "https://openmaps.gov.bc.ca/geo/pub/WHSE_LEGAL_ADMIN_BOUNDARIES.DRP_MOF_FIRE_ZONES_SP/ows"
params_zones = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeName": "WHSE_LEGAL_ADMIN_BOUNDARIES.DRP_MOF_FIRE_ZONES_SP",
    "outputFormat": "application/json",
    "CQL_FILTER": "MOF_FIRE_CENTRE_NAME='Cariboo Fire Centre'"
}
print("Fetching Cariboo Boundaries...")
response_zones = requests.get(zones_wfs_url, params=params_zones)
cariboo_gdf = gpd.read_file(BytesIO(response_zones.content))
cariboo_gdf = cariboo_gdf.to_crs(epsg=3005)

# Load Historical Fires (2012-2023)
fires_wfs_url = "https://openmaps.gov.bc.ca/geo/pub/WHSE_LAND_AND_NATURAL_RESOURCE.PROT_HISTORICAL_FIRE_POLYS_SP/ows"
params_fires = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeName": "WHSE_LAND_AND_NATURAL_RESOURCE.PROT_HISTORICAL_FIRE_POLYS_SP",
    "outputFormat": "application/json",
    "CQL_FILTER": "FIRE_YEAR >= 2012 AND FIRE_YEAR <= 2023"
}
print("Fetching Historical Fires (2012-2023). This may take a moment...")
response_fires = requests.get(fires_wfs_url, params=params_fires)
historical_fires_gdf = gpd.read_file(BytesIO(response_fires.content))

if historical_fires_gdf.crs is None:
    historical_fires_gdf = historical_fires_gdf.set_crs(epsg=3005)
else:
    historical_fires_gdf = historical_fires_gdf.to_crs(epsg=3005)

print(f"Total historical fires loaded: {len(historical_fires_gdf)}")

# Filter for Cariboo Fire Centre
print("Filtering for Cariboo Fire Centre...")
cariboo_historical_fires = gpd.sjoin(historical_fires_gdf, cariboo_gdf, how="inner", predicate="intersects")
print(f"Total historical fires in Cariboo region (2012-2023): {len(cariboo_historical_fires)}")

# Convert to EPSG:4326 (WGS84) to get standard latitude/longitude coordinates
cariboo_fires_export = cariboo_historical_fires.to_crs(epsg=4326).copy()

# Calculate centroids and extract coordinates
print("Extracting coordinates and saving to CSV...")
cariboo_fires_export['longitude'] = cariboo_fires_export.geometry.centroid.x
cariboo_fires_export['latitude'] = cariboo_fires_export.geometry.centroid.y

# Select the requested columns
columns_to_keep = ['longitude', 'latitude', 'FIRE_DATE', 'FIRE_CAUSE', 'FIRE_SIZE_HECTARES', 'FIRE_YEAR']
cariboo_csv_data = cariboo_fires_export[columns_to_keep]

# Save to CSV
csv_filename = "cariboo_historical_fires_2012_2023.csv"
cariboo_csv_data.to_csv(csv_filename, index=False)

print(f"Successfully saved {len(cariboo_csv_data)} records to {csv_filename}")

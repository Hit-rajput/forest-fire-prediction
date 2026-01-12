# Spatial Data Alignment & Mitigation of Label Noise

## 1. Problem Definition
In the development of the forest fire prediction model for the Cariboo Region, a critical data engineering challenge was identified: the geometric incompatibility between **input features** (weather data, typically accessed via rectangular bounding boxes) and **target labels** (official fire zone administrative polygons).

This mismatch creates a risk of **Spatial Label Noise**, where the model is trained on environmental data that does not spatially correspond to the ground truth of fire occurrences.

## 2. Quantitative Analysis of Spatial Error
To quantify this risk, we performed an Intersection over Union (IoU) analysis comparing the manual rectangular bounding boxes against the official BC Government *Fire Zone* shapefiles (EPSG:3005).

The analysis revealed significant error margins:

> **Findings:**
> * **Omission Error (Under-coverage):** **14.51%** of the valid fire zone territory was missed by the bounding box.
> * **Commission Error (Over-coverage):** **17.59%** of the area included in the bounding box was irrelevant land (outside the official zone).

### Impact on Model Performance
* **The 14.51% Missed:** Creates a "blind spot," reducing the model's recall (sensitivity) to fires occurring at zone peripheries.
* **The 17.59% Extra:** Introduces **Label Noise**. For example, including high-altitude mountain peaks in a valley-based fire zone dilutes the weather signal, causing the model to learn incorrect correlations between temperature and fire risk.

## 3. Theoretical Framework
This discrepancy is a manifestation of the **Modifiable Areal Unit Problem (MAUP)**, specifically the "zoning effect" (Buzzelli, 2020). 

Recent research by **Hell & Brandmeier (2024)** highlights that spatial mismatch between input rasters and vector labels is a primary source of label noise in geospatial machine learning. Their work demonstrates that failing to filter this noise significantly degrades classification accuracy by preventing the algorithm from establishing a clean decision boundary.

## 4. Implemented Solution: Polygon Masking ("Cookie Cutter")
To resolve this, we rejected the raw bounding box approach in favor of a **vector-masking pipeline**:

1.  **Fetch:** Weather data is retrieved using a super-inclusive bounding box to ensure coverage.
2.  **Mask:** A spatial join (`gpd.sjoin`) filters the retrieved weather grid points against the official BC Government polygon.
3.  **Aggregate:** Only weather points falling strictly *within* the official polygon are retained.

### Visual Verification
*(Insert your "Cookie Cutter" plot here showing the green kept points vs. red dropped points)*

![Spatial Masking Visualization](../Images/masking.png)


### Python Implementation
The following function was implemented to automate this filtering process:

```python
def filter_weather_points(weather_df, region_polygon):
    """
    Filters a DataFrame of weather points, keeping only those inside the official polygon.
    Implements the 'Cookie Cutter' approach to remove spatial label noise.
    """
    # Convert raw points to GeoDataFrame
    geometry = [Point(xy) for xy in zip(weather_df.longitude, weather_df.latitude)]
    weather_gdf = gpd.GeoDataFrame(weather_df, geometry=geometry, crs="EPSG:4326")

    # Project to BC Albers (EPSG:3005) to match official polygons
    weather_gdf = weather_gdf.to_crs("EPSG:3005")

    # Spatial Join (Keep points WITHIN polygon)
    filtered_gdf = gpd.sjoin(weather_gdf, region_polygon, how="inner", predicate="within")

    return pd.DataFrame(filtered_gdf.drop(columns=['geometry', 'index_right']))

## Phase 1 — Research notes: methodology survey and SVM dataset planning

Purpose: brief literature-grounding and an actionable plan to build the dataset needed to train and evaluate a Support Vector Machine (SVM) model for predicting wildfire occurrence in the Cariboo region (British Columbia). This document summarizes three common high‑tech methodologies for wildfire prediction, motivates why we focus on machine learning (and specifically SVM), lists candidate predictor variables (from Jaafari & Pourghasemi, 2019), proposes data sources and preprocessing steps, and outlines modelling/evaluation guidance and next steps.

### 1) High‑level methodologies used for wildfire occurrence prediction

- Physics-based (process-based) models
	- Aim: explicitly model the physical processes of fire ignition, spread, and behaviour (fuel combustion, heat transfer, atmosphere–fire coupling).
	- Strengths: interpretable physical causality, useful for fire behaviour simulation and management decisions focused on fire spread and suppression.
	- Limitations: expensive (compute, parametrisation), require detailed fuel and meteorological inputs and are not designed primarily for probabilistic occurrence mapping at regional scales.

- Statistical (classical) models
	- Aim: relate observed fire occurrences to predictor variables with parametric regression-type approaches (logistic regression, generalized linear models, point-process models).
	- Strengths: simple, interpretable coefficients, well‑understood uncertainty.
	- Limitations: may underperform when relationships are highly nonlinear or complex, require careful feature engineering and assumptions about independence.

- Machine learning methods
	- Aim: learn complex, possibly nonlinear relationships between predictors and fire occurrence from data (Random Forest, SVM, Gradient Boosting, Neural Networks, etc.).
	- Strengths: typically higher predictive performance for complex datasets, can handle many input variables, flexible feature interactions.
	- Limitations: can be less interpretable, risk of overfitting, require careful cross‑validation (spatial CV) and preprocessing.

This research: we will focus mainly on machine‑learning methods. In Phase 1 we document the ML options and start by building a dataset and baseline experiments with SVM (Support Vector Machine) inspired by Jaafari & Pourghasemi (2019), who used 28 environmental and human-related factors and compared Random Forest and SVM.

### 2) Contract — what we want from the SVM dataset and model

- Inputs: raster or vector-derived predictor variables representing vegetation indices, topography, climate, and human factors at consistent spatial resolution and projection over the Cariboo region.
- Output (dependent variable): binary label per sample (pixel or sample point): 1 = burned (presence), 0 = unburned (absence).
- Success criteria: reproducible dataset (raster stack or tabular sample set), baseline SVM trained and evaluated with clear metrics (AUC, precision/recall, F1) and spatial cross-validation to estimate generalisation.

Edge cases / risks to consider
- Strong class imbalance (burned << unburned) — must handle with sampling, class weights or resampling (SMOTE, downsampling).
- Spatial autocorrelation — naive random splitting inflates performance; use spatial cross-validation or block CV.
- Different source resolutions (MODIS vs. Landsat) — need consistent resampling and careful interpretation of derived indices.
- Missing data/clouds in optical imagery — need gap-filling or using compositing (e.g., median/percentile composites) or using radar where needed.

### 3) Key variable groups (following Jaafari & Pourghasemi, 2019)

Top variable groups (candidate predictors):

- Vegetation indices (indicator of live fuel and greenness)
	- NDVI (Normalized Difference Vegetation Index)
	- EVI (Enhanced Vegetation Index)
	- SAVI (Soil Adjusted Vegetation Index)

- Topography
	- Elevation
	- Slope
	- Aspect
	- Topographic Wetness Index (TWI)
	- Topographic Position Index (TPI)

- Climate / weather
	- Temperature (mean, max, seasonal summaries)
	- Rainfall / precipitation (total, seasonal, antecedent dryness)
	- Wind speed (climatological or recent conditions)

- Human-related / land use
	- Distance to roads
	- Distance to settlements
	- Land use / land cover (categorical)
	- Fire history (time since last fire, number of past fires)

- Fire occurrence points
	- Fire perimeters / burned area polygons converted to presence/absence labels (presence = pixel overlapped by historical burned area)

Note: Jaafari & Pourghasemi used 28 variables — the list above groups them; we will map our available layers to these groups and record any missing items.

### 4) Dependent variable definition and sampling strategy

- Binary dependent variable: 1 = burned pixel, 0 = unburned pixel (consistent with the cited paper).
- Sampling unit: pixel (raster) or point samples extracted from a raster stack. Choice driven by available raster resolution (e.g., 30 m if using Landsat) and computational budget.
- Sampling strategy recommendations:
	- For presence: sample points from historical fire perimeters (one sample per pixel inside a burned polygon). Consider stratifying by fire year or severity where available.
	- For absence: sample background points from areas outside any recorded burned polygon during the study period; avoid sampling very close to burned edges to reduce ambiguous cases.
	- Balance: maintain a reasonable presence:absence ratio for training (e.g., 1:3 to 1:5) or use class weights in the SVM.
	- Spatial CV: use spatial blocking (folds are spatially contiguous blocks) to assess generalisation to new locations.

### 5) Region & study area — Cariboo region, British Columbia

- Rationale: Cariboo experiences frequent large, complex fires, strong topography–fuel interactions, and substantial wildland–urban interface (WUI) zones — making it a good study case.
- Projection recommendation: use a BC local projection for analysis (for example BC Albers: EPSG:3005) to avoid distortion over the study area.
- Spatial extent: define an exact bounding polygon for Cariboo (use BC administrative boundaries or ecoregion polygons from BC Data Catalogue) and limit all downloads to that extent with a buffer.


- Jaafari, A., & Pourghasemi, H. R. (2019). Factors influencing regional-scale wildfire probability in Iran: An application of Random Forest and Support Vector Machine. In Spatial Modeling in GIS and R for Earth and Environmental Sciences (pp. 607–619). Elsevier. DOI: 10.1016/B978-0-12-815226-3.00028-4.
- Additional useful data sources: Copernicus (Sentinel-2, ERA5), USGS (Landsat), MODIS active fire products, SRTM/ASTER DEMs, BC Data Catalogue (provincial roads, fire perimeters, settlements).
 https://www.sciencedirect.com/science/article/pii/S2590197425000485

---



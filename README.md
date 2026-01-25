# Ishkode-Forest Fire Prediction
### *Predictive Modeling of Wildfire Intensity in the Cariboo Fire Centre*

![Status](https://img.shields.io/badge/Current_Phase-Data_Gathering_(Cariboo_Region)-orange?style=for-the-badge&logo=python)

Forest fires pose a significant threat to ecosystems, wildlife, and human lives. Early detection and accurate prediction are crucial for effective fire management. This project focuses specifically on the **Cariboo Fire Centre** in British Columbia, utilizing Machine Learning (ML) to predict fire intensity in an environment defined by unique ecological challenges.

## 📊 Project Showcase: Tableau Data Story
To effectively showcase the problem case and visualize historical data trends, we have developed an interactive **Tableau Story**. This visualization provides deep insights into the factors influencing forest fires, specifically focusing on the Canadian context.

**[➡️ Click here to view the full interactive Tableau Story](https://public.tableau.com/views/CanadianForestFIres/FInalStory?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)**

![Tableau Story Overview](Images\Dashboards\GIf_dashboard_map_area.gif)
![Additional Visual Analysis](INSERT_LINK_TO_YOUR_SECOND_GIF_HERE)

## 📍 Geographic Scope & Region Overlay
The research is strictly bounded to the **Cariboo Fire Centre**. Visualizing the specific boundaries and fire zones is critical for spatial validation.

![Cariboo Region Overlay Map](Images\Region\Region_overay.png)

*Figure 1: Overlay map detailing the Cariboo Fire Centre boundaries and relevant fire zones (Chilcotin, 100 Mile House, Quesnel, Central Cariboo) used for data sampling.*

## 🌲 Geographic & Ecological Context
This study targets the **Cariboo Fire Centre**, a massive 10.3-million-hectare administrative zone in BC's central interior. This region serves as a critical case study due to two distinct factors:
1.  **The Mountain Pine Beetle (MPB) Legacy:** Millions of hectares of lodgepole pine were compromised by the MPB infestation (peaking in the mid-2000s), creating chaotic and heavy surface fuel loads that decouple fire intensity from traditional weather predictions.
2.  **The 2017 Season Anomaly:** The analysis specifically includes the historic 2017 season, characterized by a "flash drought" and mega-fires like the **Plateau Fire** and **Elephant Hill Fire**. This "outlier class" allows us to train models to recognize the meteorological precursors to extreme fire events.

## 🎯 Objectives
- **Replication & Extension:** Replicate comparative analysis of **K-Nearest Neighbors (KNN), Decision Trees (DT), Logistic Regression (LR), and Support Vector Machines (SVM)** to validate their efficacy in the Cariboo's distinct "rain shadow" ecosystem.
- **Robust Data Engineering:** Accurately merge historical fire incident data with meteorological records using **KDTree (K-Dimensional Tree)** spatial indexing to solve the "Point-to-Point" correlation problem.
- **Intensity Proxies:** Utilize **Fire Size Class (A-E)** as a proxy for fire intensity to overcome the lack of historical flame-length data.
- **Feature Optimization:** Integrate calculated **Fire Weather Index (FWI)** components—specifically the **Drought Code (DC)**—to capture deep soil moisture deficits that drive underground burns.

## 🛠️ Methodology
The project follows a rigorous data science pipeline:
1.  **Data Acquisition (Current Phase):** Mining historical fire incidents (BC Wildfire Service) and meteorological data (Environment Canada) specifically for the Cariboo region.
2.  **Spatial Merging:** Implementing a **KDTree** algorithm to map random fire coordinates to the nearest valid "Anchor Station" (e.g., **Williams Lake A, Quesnel Airport, Puntzi Mountain, 100 Mile House**).
3.  **Algorithmic Evaluation:** Testing whether KNN retains its predictive supremacy (seen in other regions) or if the Cariboo's non-linear fire behavior favors Decision Trees.

## 📂 Dataset References
The project utilizes data from the following sources:
 - **[BC Wildfire Service Historical Fire Incidents](https://catalogue.data.gov.bc.ca/dataset/fire-incidents-historical)**: Primary vector dataset for fire locations and size classes.
 - **[Environment Canada Historical Climate Data](https://climate.weather.gc.ca/)**: Source for hourly/daily weather metrics (Temp, RH, Wind).
 - **[Canadian National Fire Database (CNFDB)](https://cwfis.cfs.nrcan.gc.ca/datamart)**
 - **[NASA MODIS Dataset](https://firms.modaps.eosdis.nasa.gov/)**

## 📄 Reference Papers
 - *Predictive Modeling of Wildfire Intensity in the Cariboo Fire Centre* (Internal Research Report).
 - [Cortez, Paulo & Morais, A. (2007). A Data Mining Approach to Predict Forest Fires using Meteorological Data.](https://www.researchgate.net/publication/238767143_A_Data_Mining_Approach_to_Predict_Forest_Fires_using_Meteorological_Data/citation/download)
 - [Shreya, M., Rai, R., Shukla, S. (2023). Forest Fire Prediction Using Machine Learning and Deep Learning Techniques.](https://doi.org/10.1007/978-981-19-3035-5_51)
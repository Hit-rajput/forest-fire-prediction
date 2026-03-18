"""
ERA5 Daily-Statistics (CDS) downloader for Cariboo Fire Centre zones.
PATCHED: Handles both ZIP and direct NetCDF downloads from CDS API.
"""

import os
import time
import zipfile
from pathlib import Path
from io import BytesIO

import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
from shapely.geometry import Point
import requests
import cdsapi


# ---------------------------
# Derived feature utilities
# ---------------------------
def kelvin_to_c(x): return x - 273.15
def wind_speed(u, v): return np.sqrt(u**2 + v**2)

def rh_from_t_td_c(t_c, td_c):
    es_t  = np.exp((17.625 * t_c)  / (243.04 + t_c))
    es_td = np.exp((17.625 * td_c) / (243.04 + td_c))
    rh = 100.0 * (es_td / es_t)
    return np.clip(rh, 0, 100)

def vpd_kpa(t_c, rh_pct):
    es = 0.6108 * np.exp((17.27 * t_c) / (t_c + 237.3))
    ea = (rh_pct / 100.0) * es
    return np.maximum(es - ea, 0.0)


# ---------------------------
# File helpers
# ---------------------------
def file_kind(path: str) -> str:
    p = Path(path)
    if (not p.exists()) or p.stat().st_size < 1000:
        return "missing_or_too_small"
    head = p.read_bytes()[:16]
    if head.startswith(b"PK"):
        return "zip"
    if head.startswith(b"\x89HDF\r\n\x1a\n") or head.startswith(b"CDF"):
        return "netcdf"
    if b"<html" in head.lower() or b"<!doctype html" in head.lower():
        return "html"
    return "unknown"

def normalize_time_column(df: pd.DataFrame) -> pd.DataFrame:
    for c in ["time", "valid_time", "date", "datetime"]:
        if c in df.columns:
            return df.rename(columns={c: "time"}) if c != "time" else df
    if getattr(df.index, "name", None) in ["time", "valid_time"]:
        idx = df.index.name
        return df.reset_index().rename(columns={idx: "time"})
    return df

def pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


# ---------------------------
# ZIP extraction + merge
# ---------------------------
def extract_zip_nc_members(zip_path: str, extract_dir: str) -> list[str]:
    os.makedirs(extract_dir, exist_ok=True)
    nc_paths = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            if name.lower().endswith(".nc"):
                out_path = os.path.join(extract_dir, os.path.basename(name))
                with z.open(name) as src, open(out_path, "wb") as dst:
                    dst.write(src.read())
                nc_paths.append(out_path)
    return nc_paths

def open_dataset_from_zip(zip_path: str, engine="netcdf4") -> xr.Dataset:
    extract_dir = zip_path + "_extracted"
    nc_files = extract_zip_nc_members(zip_path, extract_dir)
    if not nc_files:
        raise ValueError(f"No .nc files inside zip: {zip_path}")

    dsets = [xr.open_dataset(fp, engine=engine) for fp in nc_files]
    merged = xr.merge(dsets, compat="override")
    for ds in dsets:
        ds.close()
    return merged


# ---------------------------
# Main fetcher (PATCHED)
# ---------------------------
class CaribooDataFetcher:
    def __init__(self, official_zones_gdf=None, out_dir=r"C:\era5_cache", timeout=600):
        self.zones_gdf = official_zones_gdf
        self.cds_client = cdsapi.Client(timeout=timeout)
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)

    def _month_list(self, start_date, end_date):
        months = pd.period_range(pd.Timestamp(start_date).to_period("M"),
                                 pd.Timestamp(end_date).to_period("M"),
                                 freq="M")
        return [(p.year, f"{p.month:02d}") for p in months]

    def _bbox_area(self, polygon, buffer=0.25):
        poly_wgs84 = gpd.GeoSeries([polygon], crs=self.zones_gdf.crs).to_crs("EPSG:4326").iloc[0]
        minx, miny, maxx, maxy = poly_wgs84.bounds
        return [maxy + buffer, minx - buffer, miny - buffer, maxx + buffer], (minx, miny, maxx, maxy)

    def _retrieve_month_zip(self, zone_safe, year, month, daily_statistic, variables, area, time_zone):
        zone_dir = os.path.join(self.out_dir, zone_safe)
        os.makedirs(zone_dir, exist_ok=True)

        final_path = os.path.join(zone_dir, f"era5_{daily_statistic}_{year}_{month}.zip")
        tmp_path = final_path + ".part"

        # Check existing cache (allow zip or netcdf masquerading as zip)
        if os.path.exists(final_path):
            k = file_kind(final_path)
            if k in ["zip", "netcdf"]:
                print(f"   - Cached: {os.path.basename(final_path)} ({k})")
                return final_path
            else:
                try: os.remove(final_path)
                except: pass

        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass

        print(f"   > Download {year}-{month} [{daily_statistic}]...", end=" ", flush=True)

        req = {
            "product_type": "reanalysis",
            "variable": variables,
            "year": str(year),
            "month": month,
            "day": [f"{d:02d}" for d in range(1, 32)],
            "daily_statistic": daily_statistic,
            "time_zone": time_zone,
            "frequency": "1_hourly",
            "area": area,
            "data_format": "netcdf",
            "download_format": "zip",
        }

        try:
            result = self.cds_client.retrieve("derived-era5-single-levels-daily-statistics", req)
            result.download(tmp_path)
            
            # --- PATCH START: Allow NetCDF ---
            kind = file_kind(tmp_path)
            if kind not in ["zip", "netcdf"]:
                print(f"✗ (expected zip or netcdf, got {kind})")
                try: os.remove(tmp_path)
                except: pass
                return None
            
            os.replace(tmp_path, final_path)
            print(f"✓ [{kind}]")
            # --- PATCH END ---
            
            time.sleep(1)
            return final_path

        except Exception as e:
            print(f"✗ {e}")
            if os.path.exists(tmp_path):
                try: os.remove(tmp_path)
                except: pass
            return None

    def _open_zip_area_mean_df(self, zip_path: str) -> pd.DataFrame:
        # --- PATCH START: Check kind before unzip ---
        kind = file_kind(zip_path)
        
        try:
            if kind == "netcdf":
                # It's a raw NetCDF file (even if named .zip)
                try:
                    ds = xr.open_dataset(zip_path, engine="netcdf4")
                except Exception:
                    ds = xr.open_dataset(zip_path, engine="h5netcdf")
            else:
                # Assume standard ZIP
                try:
                    ds = open_dataset_from_zip(zip_path, engine="netcdf4")
                except Exception:
                    ds = open_dataset_from_zip(zip_path, engine="h5netcdf")
        except Exception as e:
            print(f"   ! Error opening {zip_path}: {e}")
            raise
        # --- PATCH END ---

        ds_mean = ds.mean(dim=["latitude", "longitude"], skipna=True)
        df = ds_mean.to_dataframe().reset_index()
        ds.close()

        df = normalize_time_column(df)
        if "time" not in df.columns:
            print("DEBUG columns:", df.columns.tolist())
            raise KeyError(f"No time/valid_time column found for {zip_path}")

        return df

    def fetch_regional_weather_era5(self, zone_name, start_date, end_date, time_zone="utc-08:00"):
        if self.zones_gdf is None:
            raise ValueError("Official Fire Zones GeoDataFrame not loaded.")

        target_zone = self.zones_gdf[self.zones_gdf["MOF_FIRE_ZONE_NAME"] == zone_name]
        if target_zone.empty:
            raise ValueError(f"Zone '{zone_name}' not found.")
        polygon = target_zone.geometry.iloc[0]

        area, (minx, miny, maxx, maxy) = self._bbox_area(polygon, buffer=0.25)

        print(f"\nFetching ERA5 daily stats for {zone_name}")
        print(f"   Date Range: {start_date} to {end_date}")
        print(f"   BBox: [{miny:.2f}..{maxy:.2f} lat, {minx:.2f}..{maxx:.2f} lon] tz={time_zone}")

        zone_safe = zone_name.replace(" ", "_").replace("/", "_").lower()
        months = self._month_list(start_date, end_date)

        mean_zips, max_zips, sum_zips = [], [], []

        for (year, month) in months:
            mean_zips.append(self._retrieve_month_zip(
                zone_safe, year, month, "daily_mean",
                ["2m_temperature", "2m_dewpoint_temperature"],
                area, time_zone
            ))
            max_zips.append(self._retrieve_month_zip(
                zone_safe, year, month, "daily_maximum",
                ["2m_temperature", "10m_u_component_of_wind", "10m_v_component_of_wind"],
                area, time_zone
            ))
            sum_zips.append(self._retrieve_month_zip(
                zone_safe, year, month, "daily_sum",
                ["total_precipitation"],
                area, time_zone
            ))

        dfs_mean = [self._open_zip_area_mean_df(z) for z in mean_zips if z]
        dfs_max  = [self._open_zip_area_mean_df(z) for z in max_zips if z]
        dfs_sum  = [self._open_zip_area_mean_df(z) for z in sum_zips if z]

        if not dfs_mean or not dfs_max or not dfs_sum:
            print("✗ Missing one of: mean/max/sum downloads; cannot build dataset.")
            return None

        df_mean = pd.concat(dfs_mean, ignore_index=True)
        df_max  = pd.concat(dfs_max,  ignore_index=True)
        df_sum  = pd.concat(dfs_sum,  ignore_index=True)

        # Column mapping
        t2m_mean_col = pick_col(df_mean, ["t2m", "2m_temperature"])
        d2m_mean_col = pick_col(df_mean, ["d2m", "2m_dewpoint_temperature"])

        t2m_max_col  = pick_col(df_max,  ["t2m", "2m_temperature"])
        u10_max_col  = pick_col(df_max,  ["u10", "10m_u_component_of_wind"])
        v10_max_col  = pick_col(df_max,  ["v10", "10m_v_component_of_wind"])

        tp_sum_col   = pick_col(df_sum,  ["tp", "total_precipitation"])

        if any(x is None for x in [t2m_mean_col, d2m_mean_col, t2m_max_col, u10_max_col, v10_max_col, tp_sum_col]):
            print("Columns in df_mean:", df_mean.columns.tolist())
            print("Columns in df_max :", df_max.columns.tolist())
            print("Columns in df_sum :", df_sum.columns.tolist())
            raise KeyError("Expected ERA5 variable columns not found. See printed columns above.")

        df_mean = df_mean[["time", t2m_mean_col, d2m_mean_col]].rename(
            columns={t2m_mean_col: "t2m_mean", d2m_mean_col: "d2m_mean"}
        )
        df_max = df_max[["time", t2m_max_col, u10_max_col, v10_max_col]].rename(
            columns={t2m_max_col: "t2m_max", u10_max_col: "u10_max", v10_max_col: "v10_max"}
        )
        df_sum = df_sum[["time", tp_sum_col]].rename(columns={tp_sum_col: "tp_sum"})

        df = df_mean.merge(df_max, on="time", how="inner").merge(df_sum, on="time", how="inner")
        df["Date"] = pd.to_datetime(df["time"])

        df["temperature_2m_mean"] = kelvin_to_c(df["t2m_mean"])
        df["temperature_2m_max"]  = kelvin_to_c(df["t2m_max"])
        df["dew_point_2m_mean"]   = kelvin_to_c(df["d2m_mean"])
        df["precipitation_sum"]   = df["tp_sum"] * 1000.0
        df["wind_speed_10m_max"]  = wind_speed(df["u10_max"], df["v10_max"])

        df["relative_humidity_2m_mean"] = rh_from_t_td_c(df["temperature_2m_mean"], df["dew_point_2m_mean"])
        df["relative_humidity_2m_min"]  = rh_from_t_td_c(df["temperature_2m_max"],  df["dew_point_2m_mean"])
        df["vpd_mean_kpa"] = vpd_kpa(df["temperature_2m_mean"], df["relative_humidity_2m_mean"])
        df["vpd_max_kpa"]  = vpd_kpa(df["temperature_2m_max"],  df["relative_humidity_2m_min"])

        out = df[[
            "Date",
            "temperature_2m_mean",
            "temperature_2m_max",
            "precipitation_sum",
            "wind_speed_10m_max",
            "relative_humidity_2m_mean",
            "relative_humidity_2m_min",
            "dew_point_2m_mean",
            "vpd_mean_kpa",
            "vpd_max_kpa",
        ]].copy()

        out = out[(out["Date"] >= pd.Timestamp(start_date)) & (out["Date"] <= pd.Timestamp(end_date))]
        out = out.sort_values("Date").reset_index(drop=True)
        return out


# ---------------------------
# Load Fire Zones (WFS)
# ---------------------------
WFS_URL = "https://openmaps.gov.bc.ca/geo/pub/WHSE_LEGAL_ADMIN_BOUNDARIES.DRP_MOF_FIRE_ZONES_SP/ows"
params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeNames": "WHSE_LEGAL_ADMIN_BOUNDARIES.DRP_MOF_FIRE_ZONES_SP",
    "outputFormat": "application/json",
    "CQL_FILTER": "MOF_FIRE_CENTRE_NAME='Cariboo Fire Centre'",
}

official_gdf = gpd.read_file(BytesIO(requests.get(WFS_URL, params=params).content))
official_gdf = official_gdf.to_crs(epsg=3005)


# ---------------------------
# Run
# ---------------------------
START_DATE = "2012-01-01"
END_DATE   = "2023-12-31"  # test month
TIME_ZONE  = "utc-08:00"

OUTPUT_DIR = "../../extracted/weather_processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

zone_list = official_gdf["MOF_FIRE_ZONE_NAME"].unique()

# IMPORTANT: cache outside OneDrive/project to avoid sync interference
fetcher = CaribooDataFetcher(official_zones_gdf=official_gdf, out_dir=r"C:\era5_cache", timeout=600)

all_zones_data = []
print(f"--- STARTING ERA5 COLLECTION ({START_DATE} to {END_DATE}) ---")
for zone in zone_list[:]:  # test first zone only
    print(f"\nPROCESSING: {zone}")
    print("=" * 40)

    df = fetcher.fetch_regional_weather_era5(zone, START_DATE, END_DATE, TIME_ZONE)

    if df is not None and not df.empty:
        df["Zone_Name"] = zone
        safe_name = zone.replace(" ", "_").replace("/", "_").lower()
        out_csv = f"{OUTPUT_DIR}/weather_{safe_name}.csv"
        df.to_csv(out_csv, index=False)
        print(f"   > Saved: {out_csv}")
        all_zones_data.append(df)
    else:
        print(f"   ! SKIPPED {zone} due to error/empty result.")

print("\n--- COMPILING MASTER DATASET ---")

if all_zones_data:
    master_df = pd.concat(all_zones_data, ignore_index=True)
    cols = ["Date", "Zone_Name"] + [c for c in master_df.columns if c not in ["Date", "Zone_Name"]]
    master_df = master_df[cols]
    master_path = f"{OUTPUT_DIR}/cariboo_master_weather_{START_DATE}_{END_DATE}.csv"
    master_df.to_csv(master_path, index=False)
    print(f"✓ MASTER DATASET SAVED: {master_path}")
else:
    print("No data collected.")

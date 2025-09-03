import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree
from typing import Tuple
from app.CONSTANTS import EARTH_RADIUS_KM

class NearestIndex:
    def __init__(self, df: pd.DataFrame):
        # Expect columns: court_id, name, borough, lat, lon
        self.df = df.reset_index(drop=True).copy()
        coords = self.df[["lat", "lon"]].to_numpy(dtype=float)
        self.coords_rad = np.radians(coords)               # (N,2) in radians
        self.tree = BallTree(self.coords_rad, metric="haversine")

    def query_k(self, lat: float, lon: float, k: int = 10) -> pd.DataFrame:
        k = min(k, len(self.df))
        q = np.radians([[lat, lon]])                      # (1,2) in radians
        dist_rad, idx = self.tree.query(q, k=k)
        dist_km = (dist_rad[0] * EARTH_RADIUS_KM)
        rows = self.df.iloc[idx[0]].copy().reset_index(drop=True)
        rows["distance_km"] = np.round(dist_km, 2)
        return rows

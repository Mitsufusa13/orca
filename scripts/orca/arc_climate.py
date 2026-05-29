"""
arc_climate.py

Wrapper around the arcclimate package for fetching MSM-based building
design climate data and converting it to EnergyPlus EPW format.

Requires:
    pip install "arcclimate @ git+https://github.com/DEE-BRI/arcclimate.git"
"""

from __future__ import annotations

import importlib
import json
import locale
import os
import site
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ARCCLIMATE_INSTALL_SPEC = "arcclimate @ git+https://github.com/DEE-BRI/arcclimate.git"


class ArcClimateClient:
    """Small facade for arcclimate init, interpolation, and EPW export."""

    LAT_MIN, LAT_MAX = 20.0, 50.0
    LON_MIN, LON_MAX = 120.0, 155.0
    YEAR_MIN, YEAR_MAX = 2011, 2020

    def __init__(self, lat, lon, year, msm_cache_dir=None):
        self.lat = float(lat)
        self.lon = float(lon)
        self.year = int(year)
        self.msm_cache_dir = self._resolve_cache_dir(msm_cache_dir)
        self._df = None
        self._arcclimate = None
        self._elevation = None

    def validate_inputs(self):
        """Validate latitude, longitude, and year for ArcClimate MSM coverage."""
        if not (self.LAT_MIN <= self.lat <= self.LAT_MAX):
            raise ValueError(
                "Latitude must be between {0} and {1} (Japan coverage). Got: {2}".format(
                    self.LAT_MIN, self.LAT_MAX, self.lat
                )
            )

        if not (self.LON_MIN <= self.lon <= self.LON_MAX):
            raise ValueError(
                "Longitude must be between {0} and {1} (Japan coverage). Got: {2}".format(
                    self.LON_MIN, self.LON_MAX, self.lon
                )
            )

        if not (self.YEAR_MIN <= self.year <= self.YEAR_MAX):
            raise ValueError(
                "Year must be between {0} and {1} (ArcClimate MSM data range). Got: {2}".format(
                    self.YEAR_MIN, self.YEAR_MAX, self.year
                )
            )

    def fetch(self):
        """
        Fetch and interpolate MSM weather data through arcclimate.

        Returns the DataFrame-like object returned by arcclimate. This module
        intentionally does not import pandas or numpy directly.
        """
        self.validate_inputs()
        arc = self._load_arcclimate()

        Path(self.msm_cache_dir).mkdir(parents=True, exist_ok=True)

        path_msm_ele, path_mesh_ele = self._get_arcclimate_data_paths(arc)
        init_result = arc.init(
            self.lat,
            self.lon,
            path_MSM_ele=path_msm_ele,
            path_mesh_ele=path_mesh_ele,
            msm_file_dir=self.msm_cache_dir,
        )
        self._elevation = self._get_target_elevation(arc, init_result)

        df = arc.interpolate(
            self.lat,
            self.lon,
            start_year=self.year,
            end_year=self.year,
            msm_elevation_master=init_result["df_msm_ele"],
            mesh_elevation_master=init_result["df_mesh_ele"],
            msms=tuple(init_result["df_msm_list"]),
            mode_elevation="api",
            mode="normal",
            use_est=True,
            vector_wind=False,
            mode_separate="Perez",
        )

        if df is None or (hasattr(df, "empty") and df.empty):
            raise RuntimeError(
                "arcclimate returned no data for lat={0}, lon={1}, year={2}".format(
                    self.lat, self.lon, self.year
                )
            )

        self._df = self._drop_leap_day(df)
        return self._df

    def to_epw(self, output_dir, filename):
        """
        Write the fetched weather data to an EPW file and return its absolute path.

        Call fetch() before this method.
        """
        if self._df is None:
            raise RuntimeError("Call fetch() before to_epw().")

        arc = self._load_arcclimate()
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = str(filename)
        out_path = out_dir / filename
        if out_path.suffix.lower() != ".epw":
            out_path = out_path.with_suffix(".epw")

        self._write_epw(arc, out_path)
        self._patch_location_header(out_path)
        return str(out_path.resolve())

    def _write_epw(self, arc, out_path):
        """Support arcclimate versions that expect either a path or a file object."""
        try:
            arc.to_epw(self._df, str(out_path), self.lat, self.lon)
            return
        except (TypeError, AttributeError):
            pass

        with out_path.open("w", encoding="utf-8", newline="") as f:
            arc.to_epw(self._df, f, self.lat, self.lon)

    def _patch_location_header(self, out_path):
        location = self._build_location_header()

        lines = out_path.read_text(encoding="utf-8").splitlines()
        if not lines:
            return

        lines[0] = (
            "LOCATION,{city},{state},{country},{source},{wmo},"
            "{lat:.6f},{lon:.6f},{timezone:.1f},{elevation:.1f}"
        ).format(**location)

        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _build_location_header(self):
        place = self._reverse_geocode()
        city = place.get("city") or "ArcClimate_{0:.4f}_{1:.4f}".format(self.lat, self.lon)
        state = place.get("state") or ""
        country = place.get("country") or "JPN"
        elevation = self._elevation if self._elevation is not None else 0.0

        return {
            "city": self._sanitize_epw_field(city),
            "state": self._sanitize_epw_field(self._normalize_state_name(state)),
            "country": self._sanitize_epw_field(country),
            "source": "ArcClimate",
            "wmo": "999999",
            "lat": self.lat,
            "lon": self.lon,
            "timezone": 9.0,
            "elevation": float(elevation),
        }

    def _get_target_elevation(self, arc, init_result):
        try:
            elevation_func = getattr(arc, "get_latlon_elevation")
            elevation = elevation_func(
                self.lat,
                self.lon,
                mode_elevation="api",
                mesh_elevation_master=init_result["df_mesh_ele"],
            )
        except Exception:
            try:
                elevation_func = getattr(arc, "get_latlon_elevation")
                elevation = elevation_func(
                    self.lat,
                    self.lon,
                    mode_elevation="mesh",
                    mesh_elevation_master=init_result["df_mesh_ele"],
                )
            except Exception:
                return None

        if elevation is None:
            return None
        return float(elevation)

    def _reverse_geocode(self):
        place = self._reverse_geocode_nominatim()
        if place:
            if not place.get("state") or place.get("country") in ("JP", "JPN"):
                gsi_place = self._reverse_geocode_gsi()
                if gsi_place:
                    place = {
                        "city": place.get("city") or gsi_place.get("city"),
                        "state": place.get("state") or gsi_place.get("state"),
                        "country": self._normalize_country_code(place.get("country") or gsi_place.get("country")),
                    }
            return place

        place = self._reverse_geocode_gsi()
        if place:
            return place

        return {}

    def _reverse_geocode_nominatim(self):
        query = urlencode(
            {
                "format": "jsonv2",
                "lat": "{0:.7f}".format(self.lat),
                "lon": "{0:.7f}".format(self.lon),
                "zoom": "10",
                "addressdetails": "1",
            }
        )
        url = "https://nominatim.openstreetmap.org/reverse?" + query
        request = Request(
            url,
            headers={
                "User-Agent": "OrcaEPWFromArchClimate/1.0",
                "Accept-Language": "en",
            },
        )

        try:
            with urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return {}

        address = payload.get("address") or {}
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
            or address.get("city_district")
        )
        state = address.get("state") or address.get("province") or address.get("region")
        country_code = address.get("country_code")
        country = self._normalize_country_code(country_code or address.get("country"))

        return {
            "city": city,
            "state": state,
            "country": country,
        }

    @staticmethod
    def _normalize_country_code(value):
        if not value:
            return None
        value = str(value).upper()
        if value == "JP":
            return "JPN"
        return value

    @staticmethod
    def _normalize_state_name(value):
        if not value:
            return value

        text = str(value).strip()
        suffixes = (
            " Prefecture",
            " prefecture",
            " Metropolitan",
            " Metropolis",
            "-ken",
            "-fu",
            "-to",
            "-do",
        )
        for suffix in suffixes:
            if text.endswith(suffix):
                text = text[: -len(suffix)].strip()
                break
        return text

    def _reverse_geocode_gsi(self):
        query = urlencode(
            {
                "lat": "{0:.7f}".format(self.lat),
                "lon": "{0:.7f}".format(self.lon),
            }
        )
        url = "https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress?" + query
        request = Request(url, headers={"User-Agent": "OrcaEPWFromArchClimate/1.0"})

        try:
            with urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return {}

        results = payload.get("results") or {}
        muni_code = str(results.get("muniCd") or "")
        prefecture = self._prefecture_name_from_muni_code(muni_code)
        city = results.get("lv01Nm") or None

        return {
            "city": city,
            "state": prefecture,
            "country": "JPN",
        }

    @staticmethod
    def _prefecture_name_from_muni_code(muni_code):
        prefectures = {
            "01": "Hokkaido", "02": "Aomori", "03": "Iwate", "04": "Miyagi",
            "05": "Akita", "06": "Yamagata", "07": "Fukushima", "08": "Ibaraki",
            "09": "Tochigi", "10": "Gunma", "11": "Saitama", "12": "Chiba",
            "13": "Tokyo", "14": "Kanagawa", "15": "Niigata", "16": "Toyama",
            "17": "Ishikawa", "18": "Fukui", "19": "Yamanashi", "20": "Nagano",
            "21": "Gifu", "22": "Shizuoka", "23": "Aichi", "24": "Mie",
            "25": "Shiga", "26": "Kyoto", "27": "Osaka", "28": "Hyogo",
            "29": "Nara", "30": "Wakayama", "31": "Tottori", "32": "Shimane",
            "33": "Okayama", "34": "Hiroshima", "35": "Yamaguchi", "36": "Tokushima",
            "37": "Kagawa", "38": "Ehime", "39": "Kochi", "40": "Fukuoka",
            "41": "Saga", "42": "Nagasaki", "43": "Kumamoto", "44": "Oita",
            "45": "Miyazaki", "46": "Kagoshima", "47": "Okinawa",
        }
        if len(muni_code) < 2:
            return None
        return prefectures.get(muni_code[:2])

    @staticmethod
    def _sanitize_epw_field(value):
        value = "" if value is None else str(value)
        return value.replace(",", " ").replace("\r", " ").replace("\n", " ").strip()

    @staticmethod
    def _get_arcclimate_data_paths(arc):
        arc_file = Path(getattr(arc, "__file__", "")).resolve()
        data_dir = arc_file.parent / "data"
        path_msm_ele = data_dir / "MSM_elevation.csv"
        path_mesh_ele = data_dir / "mesh_3d_elevation.csv"

        missing = [str(p) for p in (path_msm_ele, path_mesh_ele) if not p.is_file()]
        if missing:
            raise FileNotFoundError(
                "ArcClimate data files were not found: {0}".format(", ".join(missing))
            )

        return str(path_msm_ele), str(path_mesh_ele)

    def _load_arcclimate(self):
        if self._arcclimate is not None:
            return self._arcclimate

        self._prepare_package_imports()

        with self._base_package_import_context():
            try:
                mod = importlib.import_module("arcclimate")
            except ModuleNotFoundError:
                self._install_arcclimate()
                importlib.invalidate_caches()
                mod = importlib.import_module("arcclimate")

        if self._has_arcclimate_api(mod):
            self._arcclimate = mod
            return self._arcclimate

        with self._base_package_import_context():
            try:
                submod = importlib.import_module("arcclimate.arcclimate")
            except ModuleNotFoundError as exc:
                raise ImportError(
                    "arcclimate was found, but init/interpolate/to_epw could not be loaded."
                ) from exc

        if not self._has_arcclimate_api(submod):
            raise ImportError(
                "arcclimate does not expose the required init, interpolate, and to_epw functions."
            )

        self._arcclimate = submod
        return self._arcclimate

    @staticmethod
    def _install_arcclimate():
        if os.environ.get("ORCA_ARCCLIMATE_AUTO_INSTALL", "1").lower() in ("0", "false", "no"):
            raise ImportError(
                "arcclimate package is not installed and automatic install is disabled. "
                "Set ORCA_ARCCLIMATE_AUTO_INSTALL=1 or install manually with: "
                "{0} -m pip install \"{1}\"".format(sys.executable, ARCCLIMATE_INSTALL_SPEC)
            )

        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--trusted-host",
            "pypi.org",
            "--trusted-host",
            "files.pythonhosted.org",
            ARCCLIMATE_INSTALL_SPEC,
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
            )
        except Exception as exc:
            raise ImportError(
                "arcclimate package is not installed and automatic install failed: {0}. "
                "Install manually with: {1}".format(exc, " ".join(cmd))
            ) from exc

        if result.returncode != 0:
            details = (result.stderr or result.stdout or "").strip()
            raise ImportError(
                "arcclimate package is not installed and automatic install failed.\n"
                "Command: {0}\n{1}".format(" ".join(cmd), details)
            )

    @staticmethod
    def _prepare_package_imports():
        """
        Prefer Rhino's base site-packages over RhinoCode site-env packages.

        RhinoCode can leave partially initialized pandas/numpy modules in
        sys.modules after a failed component run. arcclimate imports both, so
        clear stale state before importing arcclimate.
        """
        base_site = ArcClimateClient._find_base_site_packages()
        if base_site.exists():
            base_site_str = str(base_site)
            sys.path[:] = [p for p in sys.path if str(p).lower() != base_site_str.lower()]
            sys.path.insert(0, base_site_str)

        ArcClimateClient._clear_modules(("pandas", "numpy"))

    @staticmethod
    @contextmanager
    def _base_package_import_context():
        original_path = list(sys.path)
        original_lc_time = None
        base_site = ArcClimateClient._find_base_site_packages()

        try:
            original_lc_time = ArcClimateClient._force_c_time_locale()

            filtered_path = []
            python_root = str(base_site.parent.parent).lower() if base_site.exists() else ""
            for p in original_path:
                p_norm = str(p).lower().replace("/", "\\")
                if "\\site-envs\\" in p_norm:
                    continue
                if "ladybug_tools\\python" in p_norm:
                    continue
                if "\\program files\\ladybug_tools\\" in p_norm:
                    continue
                if "\\lib\\site-packages" in p_norm and python_root and python_root not in p_norm:
                    continue
                filtered_path.append(p)
            if base_site.exists():
                base_site_str = str(base_site)
                filtered_path = [
                    p for p in filtered_path
                    if str(p).lower() != base_site_str.lower()
                ]
                filtered_path.insert(0, base_site_str)

            sys.path[:] = filtered_path
            ArcClimateClient._clear_modules(("pandas", "numpy", "arcclimate"))
            importlib.invalidate_caches()
            yield
        finally:
            sys.path[:] = original_path
            ArcClimateClient._restore_time_locale(original_lc_time)

    @staticmethod
    def _force_c_time_locale():
        try:
            current = locale.setlocale(locale.LC_TIME)
        except Exception:
            current = None

        try:
            locale.setlocale(locale.LC_TIME, "C")
        except Exception:
            pass

        return current

    @staticmethod
    def _restore_time_locale(locale_name):
        if not locale_name:
            return
        try:
            locale.setlocale(locale.LC_TIME, locale_name)
        except Exception:
            # RhinoCode may report Windows/.NET-style values such as ja-JP,
            # which Python 3.9's locale parser cannot restore reliably.
            pass

    @staticmethod
    def _find_base_site_packages():
        candidates = []

        for root in (
            getattr(sys, "prefix", None),
            getattr(sys, "base_prefix", None),
            getattr(sys, "exec_prefix", None),
        ):
            if root:
                candidates.append(Path(root) / "Lib" / "site-packages")
                candidates.append(Path(root) / "lib" / "site-packages")

        try:
            candidates.extend(Path(p) for p in site.getsitepackages())
        except Exception:
            pass

        for p in sys.path:
            p_str = str(p)
            p_norm = p_str.lower().replace("/", "\\")
            if "\\.rhinocode\\py39-rh8\\lib\\site-packages" in p_norm:
                candidates.append(Path(p_str))

        for candidate in candidates:
            if candidate.exists() and (candidate / "numpy").exists() and (candidate / "pandas").exists():
                return candidate

        return Path(sys.prefix) / "Lib" / "site-packages"

    @staticmethod
    def _clear_modules(root_names):
        names = [
            name for name in sys.modules
            if any(name == root or name.startswith(root + ".") for root in root_names)
        ]
        for name in sorted(names, key=lambda value: value.count("."), reverse=True):
            sys.modules.pop(name, None)

    @staticmethod
    def _has_arcclimate_api(mod):
        return (
            hasattr(mod, "init")
            and hasattr(mod, "interpolate")
            and hasattr(mod, "to_epw")
        )

    @staticmethod
    def _resolve_cache_dir(msm_cache_dir):
        if msm_cache_dir:
            return str(msm_cache_dir)

        env = os.environ.get("ARCCLIMATE_CACHE_DIR")
        if env:
            return env

        appdata = os.environ.get("APPDATA")
        if appdata:
            return str(Path(appdata) / "arcclimate" / "msm_cache")

        return str(Path.home() / ".arcclimate" / "msm_cache")

    @staticmethod
    def _drop_leap_day(df):
        """Remove February 29 rows when the returned object has a DatetimeIndex."""
        idx = getattr(df, "index", None)
        if not (hasattr(idx, "month") and hasattr(idx, "day")):
            return df

        leap_mask = (idx.month == 2) & (idx.day == 29)
        if hasattr(leap_mask, "any") and leap_mask.any():
            return df.loc[~leap_mask].copy()

        return df

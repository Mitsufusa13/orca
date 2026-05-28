# Changelog

All notable changes to this project will be documented in this file.
このプロジェクトへの変更はすべてこのファイルに記録されます。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

---

## [0.1.0] - 2025-05-28

### Added / 追加
- Initial public release of Orca Grasshopper plugin
- 48 UserObject components across 8 categories (CreateGeometry, EnergyPlusObject, ConstructionAndMaterial, Condition, Schedule, ZoneHVAC, EnergyPlus, Others)
- Python library (`scripts/orca/`) for EnergyPlus model building and simulation

### Fixed / 修正
- **P0** `OrcaRunEnergyPlus`: Fixed `run` variable NameError when `_run` is connected before path inputs
- **P0** `OrcaValuesFromSQL`: Added `Variable is not None` guard
- **P0** `OrcaCalculateUA`: Fixed variable shadowing in surface loop
- **P0** `OrcaAddZoneHVAC`: Fixed indentation causing `_zonehvac` NameError
- **P0** `OrcaWindowBrepfromHW/WWR`: Added `Index = 0` default guard
- **P0** `OrcaToIDF`: Nested `if _run:` inside file path guard
- **P0** `OrcaCalculateProperties`: Added `Thickness is not None` guard
- **P0** `scripts/orca/brepnormalize.py`: Fixed `10-6` → `1e-6` in two functions
- **P0** `scripts/orca/ghutil.py`: Fixed misplaced closing bracket in `_unwrap_point_list`
- **P0** `scripts/orca/foundation.py`: Restored broken class definition
- **P1** `OrcaAddLights`, `OrcaAddElectricEquipment`: Added `float()` cast for watt inputs
- **P1** `OrcaAddZoneInfiltration`: Fixed typo `infilatration` → `infiltration`
- **P1** `OrcaIdeaLoadsAirSystem`: Fixed typo `defumidification` → `dehumidification`
- **P1** `scripts/orca/schedule.py`: Fixed key `End_Day_1_{n}` → `End_Day_{n}`
- **P1** `scripts/orca/model.py`: Fixed `Color.FromArgb(0.99,...)` float alpha → integer `0`
- **P1** `scripts/orca/model.py`, `zones.py`: Fixed list mutation bug in `vertices()` return value
- **P1** `scripts/orca/zonehvac_ideal_loads_air_system.py`: Fixed `LimitCapacity` branch condition
- **P2** `ConstructionAndMaterial/04–06`: Changed `type(x) != float` to `isinstance(x, (int, float))`
- **P2** `OrcaShading`: Removed no-op self-assignment
- **P2** `OrcaWindow`: Removed redundant `if WindowType is not None:`
- **P2** `OrcaZoneBrep`: Added `None` guard for `Width`, `Depth`, `Height`
- **P2** `OrcaShadingControl`: Added `try/except ImportError` around import
- **P2** `OrcaZoneControlThermostat`: Changed `if control_type_schedule:` to `is not None`
- **P2** `scripts/orca/zone.py`, `zones.py`, `model.py`: Fixed HVAC dict key typo `ThemostatSetointDual` → `ThermostatSetpointDual`
- **P2** `scripts/orca/epw.py`: Fixed leap year to full Gregorian rule
- **P3** `scripts/orca/brep.py`: Removed debug prints; fixed `serach_wall_brep` → `search_wall_brep`
- **P3** `scripts/orca/construction.py`: Removed dead `else` branch; added `__resistance = None` init
- **P3** `scripts/orca/idf.py`: Fixed `delete_triling_whitespace` typo; replaced bare `except:`
- **P3** `scripts/orca/energyplus_class.py`: Removed unused `ClassName` template class
- **P3** `scripts/orca/run_energyplus.py`: Replaced hardcoded path with `set_energyplus_dir()` and `ENERGYPLUS_DIR` env var
- **P3** All UserObject files: Replaced bare `except:` with `except ImportError:`
- **P3** Moved `get_idd_data.py`, `test.py` to `scripts/orca/dev/`

<p align="center">
  <img src="images/orca_logo.png" alt="Orca Logo" width="120">
</p>

# Orca

**Grasshopper plugin for EnergyPlus building energy simulation**
**EnergyPlusによる建物エネルギーシミュレーション用 Grasshopper プラグイン**

---

## Overview / 概要

Orca is a Grasshopper (Rhino 8) plugin that provides Python 3 components for building energy simulation using EnergyPlus. It allows you to create zone geometry, define construction and materials, set occupancy conditions, configure HVAC systems, and run simulations — all within the Grasshopper visual programming environment.

Orca は、EnergyPlus を使った建物エネルギーシミュレーションのための Grasshopper（Rhino 8）プラグインです。ゾーンジオメトリの作成、構造・材料の定義、在室条件の設定、HVAC システムの構成、シミュレーションの実行を、Grasshopper のビジュアルプログラミング環境内で完結して行うことができます。

---

## Requirements / 動作環境

| Item | Version |
|---|---|
| Rhino | 8.x |
| Grasshopper | Built-in (Rhino 8) |
| EnergyPlus | 24.2.0 or compatible |
| Python | 3.x (CPython via ScriptParasite) |
| arcclimate *(optional)* | Latest — required only for `OrcaEPWFromArchClimate` |

> **`OrcaEPWFromArchClimate` を使用する場合**: Grasshopper の CPython 環境に `arcclimate` パッケージをインストールしてください。
> ```
> pip install arcclimate
> ```

---

## Installation / インストール

### 0. Download / ダウンロード

Download `Orca.gh` from the [Releases](../../releases) page or directly from the root of this repository.

このリポジトリのルートにある `Orca.gh`、または [Releases](../../releases) ページからダウンロードしてください。

### 1. Install via Orca.gh / Orca.gh を使ったインストール（推奨）

Open `Orca.gh` in Grasshopper. Double-click the **Toggle** component to set it to `True` — this will start the installation and automatically copy the required scripts and UserObjects to the correct directories.

`Orca.gh` を Grasshopper で開き、**Toggle** コンポーネントをダブルクリックして `True` にしてください。インストールが開始され、必要なスクリプトとユーザーオブジェクトが自動的に正しいディレクトリにコピーされます。

After the installer completes, restart Rhino/Grasshopper. The **Orca** tab will appear in the component panel.
インストール完了後、Rhino / Grasshopper を再起動してください。コンポーネントパネルに **Orca** タブが表示されます。

---

### Manual Installation / 手動インストール

If you prefer to install manually, follow the steps below.
手動でインストールする場合は、以下の手順に従ってください。

#### a. Python library / Python ライブラリ

Copy the `scripts/orca` folder to your Grasshopper Python path:

`scripts/orca` フォルダを Grasshopper の Python パスが通っている場所にコピーしてください。

```
%APPDATA%\McNeel\Rhinoceros\8.0\scripts\
```

After copying, the folder structure should be:
コピー後のフォルダ構成:

```
scripts/
  orca/
    __init__.py
    brep.py
    model.py
    zone.py
    ...
```

#### b. User Objects / ユーザーオブジェクト

Copy the `UserObjects/Orca` folder to your Grasshopper UserObjects directory:

`UserObjects/Orca` フォルダを Grasshopper のユーザーオブジェクトディレクトリにコピーしてください。

```
%APPDATA%\Grasshopper\UserObjects\
```

After restarting Rhino/Grasshopper, the **Orca** tab will appear in the component panel.
Rhino / Grasshopper を再起動すると、コンポーネントパネルに **Orca** タブが表示されます。

### 2. EnergyPlus

Download and install EnergyPlus from the official site. By default, Orca looks for the installation at `C:/EnergyPlusV{version}`. You can override this by setting the environment variable:

EnergyPlus を公式サイトからダウンロードしてインストールしてください。デフォルトでは `C:/EnergyPlusV{バージョン}` を参照します。環境変数で変更できます：

```
ENERGYPLUS_DIR=C:/path/to/your/EnergyPlus
```

---

## Samples / サンプル

The `samples/` folder contains example Grasshopper files demonstrating typical workflows.

`samples/` フォルダに、代表的なワークフローを示すサンプルファイルが含まれています。

| File | Description |
|---|---|
| ArcClimate.gh | — |

---

## Components / コンポーネント一覧

### CreateGeometry — ジオメトリ作成

| Component | Description |
|---|---|
| OrcaZoneBrep | Create a box-shaped zone Brep from a reference point and dimensions |
| OrcaAtticBrep | Create an attic zone Brep from a roof surface |
| OrcaWindowBrepfromHW | Create a window Brep on a wall by specifying width and height |
| OrcaWindowBrepfromWWR | Create a window Brep on a wall by specifying window-to-wall ratio |

### EnergyPlusObject — EnergyPlus オブジェクト

| Component | Description |
|---|---|
| OrcaZone | Define an EnergyPlus zone from a Brep |
| OrcaWindow | Define a window surface |
| OrcaShading | Define a shading surface |
| OrcaAddWindow | Add a window to a zone |
| OrcaAddShading | Add a shading surface to a model |
| OrcaAddConstructionSet | Assign a construction set to a zone |
| OrcaModel | Assemble zones into a building model |

### ConstructionAndMaterial — 構造・材料

| Component | Description |
|---|---|
| OrcaConstructionSet | Define a construction set for a zone |
| OrcaConstruction | Define an opaque construction (layer stack) |
| OrcaConstructionWindow | Define a window construction |
| OrcaOpaqueMaterial | Define an opaque material |
| OrcaOpaqueMaterialNoMass | Define a no-mass opaque material |
| OrcaMaterialSimpleGlazingSystem | Define a simple glazing system |
| OrcaWindowMaterialGlazing | Define a detailed glazing material |
| OrcaWindowMaterialGas | Define a window gas layer |
| OrcaWindowMaterialShade | Define a window shade material |
| OrcaWindowPropertyFrameAndDivider | Define window frame and divider properties |
| OrcaShadingControl | Define shading control for a window |

### Condition — 内部発熱・換気

| Component | Description |
|---|---|
| OrcaAddPeople | Add occupancy (people) to a zone |
| OrcaAddLights | Add lighting to a zone |
| OrcaAddElectricEquipment | Add electric equipment to a zone |
| OrcaAddZoneInfiltration | Add infiltration to a zone |

### Schedule — スケジュール

| Component | Description |
|---|---|
| OrcaScheduleTypelimits | Define schedule type limits |
| OrcaScheduleDayInterval | Define a day schedule by intervals |
| OrcaScheduleWeekDaily | Define a week schedule from day schedules |
| OrcaScheduleYear | Define a year schedule from week schedules |

### ZoneHVAC — HVAC

| Component | Description |
|---|---|
| OrcaAddZoneHVAC | Add HVAC objects to a zone |
| OrcaIdeaLoadsAirSystem | Define an ideal loads air system |
| OrcaZoneControlThermostat | Define thermostat control for a zone |
| OrcaThermostatSetpointDual | Define dual setpoint thermostat |
| OrcaZoneControlHumidistat | Define humidistat control for a zone |

### EnergyPlus — シミュレーション実行

| Component | Description |
|---|---|
| OrcaToIDF | Export the model to an EnergyPlus IDF file |
| OrcaRunEnergyPlus | Run an EnergyPlus simulation |
| OrcaSearchEPClass | Search available EnergyPlus classes |
| OrcaEPClassObject | Create a generic EnergyPlus object |
| OrcaReadIDF | Read an existing IDF file |
| OrcaReadSQL | Read simulation results from a SQL file |
| OrcaValuesFromSQL | Extract specific variable values from SQL results |

### Others — ユーティリティ

| Component | Description |
|---|---|
| OrcaChangeSurfaceOBC | Change the outside boundary condition of a surface |
| OrcaCalculateUA | Calculate the UA value of a zone |
| OrcaCalculateProperties | Calculate thermal properties of a construction |
| OrcaReadEPW | Read EPW weather file data |
| OrcaCalculateACPeriod | Calculate air-conditioning period from EPW data |
| OrcaArcClimate2EPW | Convert ArcClimate CSV data to EPW format |
| OrcaEPWFromArchClimate | Fetch building design climate data from ArcClimate by latitude/longitude and generate an EPW file |

---

## License / ライセンス

See [LICENSE](LICENSE) for details.
ライセンスの詳細は [LICENSE](LICENSE) を参照してください。

---

## Changelog / 変更履歴

See [CHANGELOG.md](CHANGELOG.md).

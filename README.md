# 🚀 Lunar Ice Mission Planner
### Chandrayaan-2 DFSAR + OHRC Analysis Platform
#### Bharatiya Antariksh Hackathon — ISRO

---

## 🌙 Overview

The **Lunar Ice Mission Planner** is an end-to-end automated mission analysis platform built for the Bharatiya Antariksh Hackathon. It processes real Chandrayaan-2 satellite data — DFSAR radar and OHRC high-resolution imagery — to detect water-ice deposits near the lunar south pole, identify safe landing sites, and plan an optimal rover path to the ice.

Everything runs locally in your browser via Streamlit. No internet connection required after setup.

---

## 🎯 What It Does

| Step | Module | Output |
|------|--------|--------|
| 1. Load radar data | `radar_processor.py` | HH / HV polarization arrays |
| 2. Compute CPR | `radar_processor.py` | Circular Polarization Ratio map |
| 3. Compute DOP | `radar_processor.py` | Degree of Polarization map |
| 4. Detect ice | `radar_processor.py` | Ice mask + probability map |
| 5. Analyze terrain | `terrain_analyzer.py` | Slope, roughness, hazard maps |
| 6. Select landing site | `terrain_analyzer.py` | Optimal safe landing coordinates |
| 7. Plan rover path | `rover_path.py` | A* optimal path to ice deposit |
| 8. Generate report | `report_generator.py` | Downloadable PDF mission report |

---

## 🧊 The Science

### Circular Polarization Ratio (CPR)
CPR = HV / HH
CPR > 1.0 indicates anomalously high cross-polarized backscatter — the primary radar signature of water ice, consistent with findings from Chandrayaan-1 Mini-RF and the Spudis et al. (2013) lunar ice study.

### Degree of Polarization (DOP)
DOP = (HH − HV) / (HH + HV)
Low DOP (< 0.3) in permanently shadowed regions (PSRs) corroborates the ice interpretation. The combination of **high CPR + low DOP** is the strongest dual-indicator of subsurface ice.

### Ice Volume Estimation
Detected ice area is converted to volume assuming a conservative **2-metre depth** and ice density of **917 kg/m³** to yield a water-equivalent mass in tonnes.

### Landing Site Scoring
A weighted model scores every pixel:
Score = (Ice Proximity × 0.35) + (Safety × 0.40) + (Ice Probability × 0.25)
Sites with slope > 15° or hazard index > 0.7 are automatically excluded.

### Rover Pathfinding (A*)
The A* algorithm finds the shortest safe path from the landing site to the nearest ice deposit, penalising high-slope and high-hazard terrain in the cost function.

---

## 📁 Project Structure
Lunar-Ice-Mission/

│

├── app.py                          # Main Streamlit application

│

├── modules/

│   ├── radar_processor.py          # CPR, DOP, ice detection, volume estimation

│   ├── terrain_analyzer.py         # Slope, roughness, hazard, landing site selection

│   ├── rover_path.py               # A* pathfinding + path metrics

│   └── report_generator.py         # PDF mission report (ReportLab)

│

├── data/

│   ├── dfsar/                      # Place DFSAR radar files here (.tif / .img / .zip)

│   └── ohrc/                       # Place OHRC image files here (.tif / .img / .zip)

│

├── reports/                        # Auto-generated PDF reports saved here

├── output/                         # Optional processed output files

├── assets/                         # Logos, images, static assets

│

├── .streamlit/

│   └── config.toml                 # Raises upload limit to 1 GB for large datasets

│

├── requirements.txt                # Python dependencies

└── README.md                       # This file


# Requirements for this Project

This project requires **Python 3.10+** (recommended) along with the following Python packages.

## Dependencies

| Package        | Minimum Version | Purpose                                                  |
| -------------- | --------------: | -------------------------------------------------------- |
| **Streamlit**  |        `1.35.0` | Interactive web application framework                    |
| **NumPy**      |        `1.26.0` | Numerical computing and array operations                 |
| **Matplotlib** |         `3.8.0` | Data visualization and plotting                          |
| **OpenCV**     |         `4.9.0` | Image processing and computer vision                     |
| **Rasterio**   |         `1.3.0` | Reading and processing geospatial raster data            |
| **SciPy**      |        `1.13.0` | Scientific computing and advanced mathematical functions |
| **Pillow**     |        `10.0.0` | Image loading, manipulation, and saving                  |
| **ReportLab**  |         `4.2.0` | PDF generation and report creation                       |

## Installation

Install all dependencies using:

```bash
pip install -r requirements.txt
```

or install them individually:

```bash
pip install \
streamlit>=1.35.0 \
numpy>=1.26.0 \
matplotlib>=3.8.0 \
opencv-python>=4.9.0 \
rasterio>=1.3.0 \
scipy>=1.13.0 \
pillow>=10.0.0 \
reportlab>=4.2.0
```

## Python VersioN

This project is tested with:

* Python **3.10**
* Python **3.11**
* Python **3.12**

Newer versions may also work but have not been officially tested.

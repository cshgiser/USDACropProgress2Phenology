# USDACropProgress2Phenology

A specialized tool for extracting crop phenology (Day of Year) and developmental intervals from USDA NASS Crop Progress reports.

## Overview

The **USDACropProgress2Phenology** repository provides a workflow to convert original USDA NASS weekly reports into structured phenological metrics. It transforms cumulative area proportions into:
* **Phenology (DOY):** The estimated Day of Year (1–365/366) when a crop reaches a specific growth stage.
* **Intervals:** The duration (number of days) between different growing stages.

## Background

The USDA NASS Crop Progress data provides weekly updates on the percentage of crop area reaching specific stages (e.g., Planted, Silking, Harvested) by state. However, because these data are reported as weekly snapshots of cumulative area, they require processing to determine the actual mean date of occurrence.

### Data Processing Logic

To achieve high-accuracy phenology extraction, this tool applies the following methodology:

1.  **Temporal Mid-point Shift:** Since NASS reports reflect the area proportion reached by the *end* of a reporting week, the code applies a **3-day shift** to the middle of the week. This better represents the average time the area reached that stage.
2.  **Weighted Average Calculation:** The tool treats the weekly increase in area proportion as weights to calculate the weighted average DOY for each specific growth stage.
3.  **Interval Calculation:** Using the calculated DOYs, the tool automatically computes the number of days elapsed between consecutive stages.

---

## Example Transformation

### 1. Input: Cumulative Area Time Series
The tool processes raw cumulative percentages. For example, **Corn in Wisconsin (2018)**:

| Date | Corn - Planted | Corn - Silking | Corn - Harvested |
| :--- | :---: | :---: | :---: |
| 4/29/2018 | 3% | - | - |
| 7/15/2018 | 100% | 30% | - |
| 11/25/2018 | 100% | 100% | 88% |

### 2. Output: Extracted Phenology (DOY)
The final output provides the specific DOY for each stage:

| Crop Stage | 2018 (DOY) |
| :--- | :--- |
| **Corn - Planted** | 136.45 |
| **Corn - Emerged** | 147.57 |
| **Corn - Silking** | 200.64 |
| **Corn - Dough** | 224.09 |
| **Corn - Dented** | 242.69 |
| **Corn - Mature** | 263.08 |
| **Corn - Harvested** | 299.51 |

---

## Usage

Please refer to the source code for specific implementation details on the weighting algorithm and data cleaning procedures. 

## Contact

If you have questions or need assistance, please contact: [scai62@wisc.edu](mailto:scai62@wisc.edu) or [csh_giser@163.com](mailto:csh_giser@163.com)

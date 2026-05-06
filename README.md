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

### Example: Accumulated Area Proportion Time Series
*Example data for Corn in Wisconsin, 2018. Values represent the percentage of total cornfield area reaching each stage.*

| Date | Corn - Dented | Corn - Dough | Corn - Emerged | Corn - Harvested | Corn - Mature | Corn - Planted | Corn - Silking |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 4/29/2018 | | | | | | 3 | |
| 5/6/2018 | | | | | | 15 | |
| 5/13/2018 | | | 8 | | | 30 | |
| 5/20/2018 | | | 21 | | | 56 | |
| 5/27/2018 | | | 48 | | | 81 | |
| 6/3/2018 | | | 75 | | | 89 | |
| 6/10/2018 | | | 87 | | | | |
| 6/17/2018 | | | 96 | | | | |
| 6/24/2018 | | | | | | | |
| 7/1/2018 | | | | | | | 1 |
| 7/8/2018 | | | | | | | 6 |
| 7/15/2018 | | | | | | | 30 |
| 7/22/2018 | | | | | | | 53 |
| 7/29/2018 | | 8 | | | | | 76 |
| 8/5/2018 | | 28 | | | | | 87 |
| 8/12/2018 | 4 | 45 | | | | | |
| 8/19/2018 | 18 | 62 | | | | | |
| 8/26/2018 | 36 | 77 | | | 1 | | |
| 9/2/2018 | 54 | 86 | | | 8 | | |
| 9/9/2018 | 70 | | | | 21 | | |
| 9/16/2018 | 82 | | | 1 | 36 | | |
| 9/23/2018 | 91 | | | 4 | 55 | | |
| 9/30/2018 | | | | 10 | 73 | | |
| 10/7/2018 | | | | 14 | 84 | | |
| 10/14/2018 | | | | 19 | 93 | | |
| 10/21/2018 | | | | 31 | | | |
| 10/28/2018 | | | | 46 | | | |
| 11/4/2018 | | | | 59 | | | |
| 11/11/2018 | | | | 69 | | | |
| 11/18/2018 | | | | 80 | | | |
| 11/25/2018 | | | | 88 | | | |

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

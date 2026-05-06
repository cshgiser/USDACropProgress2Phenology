import os
import zipfile
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import re
import unicodedata
from datetime import timedelta
import numpy as np

crop_results = {}

def clean_and_extract_stage(description, crop):
    # 1. Normalize the string to NFKD form, which breaks down
    # weird characters (like \x96) into their standard components
    # then encode/decode to remove anything that isn't standard ASCII
    safe_desc = unicodedata.normalize('NFKD', description).encode('ascii', 'ignore').decode('ascii')

    # 2. Now that the string is 'clean' ASCII, remove the crop name
    clean_desc = re.sub(re.escape(crop), '', safe_desc, flags=re.IGNORECASE).strip()

    # 3. Split by any sequence of non-alphanumeric characters (dashes, spaces, etc.)
    # This splits by any character that isn't a letter or number,
    # then takes the first meaningful part.
    parts = re.split(r'[^a-zA-Z0-9]+', clean_desc)

    # 4. Return the first part (the stage)
    return parts[0].strip()

def read_html_file(index_path):
    """Attempts to read with utf-8 first, then falls back to ISO-8859-1."""
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return BeautifulSoup(f, 'html.parser')
    except UnicodeDecodeError:
        print(f"UTF-8 failed for {index_path.name}, trying ISO-8859-1...")
        with open(index_path, 'r', encoding='ISO-8859-1') as f:
            return BeautifulSoup(f, 'html.parser')

def parse_date(month_day_str, year_str):
    """Converts 'April 10,' and '2016' into '04/10/2016'"""
    try:
        clean_str = f"{month_day_str.strip()} {year_str.strip()}".replace(',', '')
        dt = datetime.strptime(clean_str, "%B %d %Y")
        return dt.strftime("%m/%d/%Y")
    except:
        return f"{month_day_str} {year_str}".strip()


def process_csv(csv_path, crop_type, stage):
    # Try common encodings for USDA files
    encodings = ['utf-8', 'ISO-8859-1', 'cp1252']
    df = None

    for enc in encodings:
        try:
            df = pd.read_csv(
                csv_path,
                sep=',',
                header=None,
                names=range(20),
                engine='python',
                encoding=enc
            )
            break  # If successful, stop trying other encodings
        except:
            continue

    # If all encodings failed, use the "nuclear option": replace bad bytes with '?'
    if df is None:
        try:
            df = pd.read_csv(
                csv_path,
                sep=',',
                header=None,
                names=range(20),
                engine='python',
                encoding='ISO-8859-1',
                encoding_errors='replace'
            )
        except Exception as e:
            print(f"Could not read {csv_path.name}: {e}")
            return

    try:
        # Now, since we have 20 columns, we can reliably find the markers
        # The 'd' column is index 1, the state is index 2, data is index 5
        data_rows = df[(df[1] == 'd')]

        # Find the date row (search for the 'Week ending' text across the whole df)
        # We look for the first row containing 'Week ending'
        date_mask = df.apply(lambda row: row.astype(str).str.contains('Week ending'), axis=1)
        if not date_mask.any().any(): return

        # Get index of first occurrence
        date_row_idx = date_mask.any(axis=1).idxmax()

        # The 3rd 'Week ending' header is at column index 5 (based on your notepad view)
        data_col_idx = 5

        month_day = str(df.iloc[date_row_idx + 2, data_col_idx])
        year = str(df.iloc[date_row_idx + 3, data_col_idx])
        final_date = parse_date(month_day, year)

        # Extract data
        for _, row in data_rows.iterrows():
            state = str(row[2])
            val = str(row[data_col_idx])

            # Simple numeric filter
            if state in ['nan', '18 States', ''] or val in ['nan', '(NA)', '-', '']:
                continue

            # Clean values like "2" or "24"
            clean_val = ''.join(c for c in val if c.isdigit() or c == '.')
            if clean_val:
                key = (state, crop_type, stage, final_date)
                crop_results[key] = float(clean_val)

    except Exception as e:
        print(f"Error processing {csv_path.name}: {e}")


def extract_zip_files(source_dir, destination_dir):
    source_path = Path(source_dir)
    dest_path = Path(destination_dir)

    # Create destination directory if it doesn't exist
    dest_path.mkdir(parents=True, exist_ok=True)

    # Find all zip files in the source directory
    zip_files = list(source_path.glob("*.zip"))

    if not zip_files:
        print(f"No zip files found in {source_dir}")
        return

    for file_path in zip_files:
        # Create a folder name based on the zip file name (without extension)
        target_folder = dest_path / file_path.stem

        print(f"Extracting: {file_path.name} -> {target_folder}")

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(target_folder)
        except zipfile.BadZipFile:
            print(f"Error: {file_path.name} is corrupted or not a valid zip file.")
        except Exception as e:
            print(f"An error occurred with {file_path.name}: {e}")

    print("\nExtraction complete.")


def export_results_to_csv(results, output_dir):
    # 1. Convert the dictionary into a DataFrame
    df = pd.DataFrame([
        {'State': k[0], 'Crop': k[1], 'Stage': k[2], 'Date': pd.to_datetime(k[3]), 'Percent': v}
        for k, v in results.items()
    ])

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 2. Group by State
    for state, group in df.groupby('State'):
        # 3. Create a unique column name: "Crop - Stage"
        group['Crop_Stage'] = group['Crop'] + ' - ' + group['Stage']

        # 4. Pivot the table: Dates as rows, Crop_Stage as columns
        pivot_df = group.pivot(index='Date', columns='Crop_Stage', values='Percent')

        # 5. Sort by Date
        pivot_df = pivot_df.sort_index()

        # 6. Save to CSV
        file_name = f"{state.replace(' ', '_')}_progress.csv"
        pivot_df.to_csv(Path(output_dir) / file_name)
        print(f"Exported: {file_name}")



def calculate_weighted_doy(group):
    """Calculates the weighted average DOY for a crop stage group."""
    # Calculate daily increments
    increments = group['Percent'].diff().fillna(group['Percent']).clip(lower=0)
    total_percent = increments.sum()

    if total_percent == 0:
        return np.nan

    # Weighted average: Sum(Percent * DOY) / Total Percent
    return (increments * group['DOY']).sum() / total_percent


def extract_phenology_doy_state_files(source_dir, output_dir):
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for csv_file in source_path.glob("*.csv"):
        print(f"Processing: {csv_file.name}")
        df = pd.read_csv(csv_file, parse_dates=['Date'])

        # (2) Overall shift: Minus 3 days
        df['Date'] = df['Date'] - timedelta(days=3)

        # (1) Generate Year and DOY
        df['Year'] = df['Date'].dt.year
        df['DOY'] = df['Date'].dt.dayofyear

        # Reshape to long format to facilitate grouping
        df_long = df.melt(id_vars=['Date', 'Year', 'DOY'], var_name='Crop_Stage', value_name='Percent')

        results = []

        # Group by Year and Crop_Stage
        for (year, stage), group in df_long.groupby(['Year', 'Crop_Stage']):
            avg_doy = calculate_weighted_doy(group)
            results.append({
                'Year': year,
                'Crop_Stage': stage,
                'Avg_DOY': avg_doy
            })

        # Create summary DataFrame
        summary_df = pd.DataFrame(results)

        # (5) Pivot so Years are columns
        final_pivot = summary_df.pivot(index='Crop_Stage', columns='Year', values='Avg_DOY')

        # Export
        final_pivot.to_csv(output_path / f"Summary_{csv_file.name}")



def calculate_intervals(summary_file, crop_orders):
    df = pd.read_csv(summary_file, index_col='Crop_Stage')
    all_intervals = []

    # Process by Crop
    for crop, stages in crop_orders.items():
        # Filter stages found in the file
        found_stages = [s for s in stages if f"{crop} - {s}" in df.index]

        # Calculate intervals
        for i in range(len(found_stages) - 1):
            s1, s2 = f"{crop} - {found_stages[i]}", f"{crop} - {found_stages[i + 1]}"
            interval = df.loc[s2] - df.loc[s1]
            interval.name = f"{crop}_{found_stages[i]}_to_{found_stages[i + 1]}"
            all_intervals.append(interval)

    return pd.DataFrame(all_intervals)


if __name__ == '__main__':
    print(os.getcwd())

    # Configuration
    base_dir = Path(r"...\Original_zipfiles")
    target_crops = ["Corn", "Soybeans", "Spring Wheat"]

    # Dictionary to store data: {(state, crop, stage, date): percent}
    crop_data = {}

    # 1. Find all subfolders
    subfolders = [f for f in base_dir.iterdir() if f.is_dir()]

    for folder in subfolders:
        print(f"Processing {folder.name}")
        # 2. Specifically look for 'prog_index.htm'
        index_file = folder / "prog_index.htm"

        if not index_file.exists():
            # Skip this folder if the index file doesn't exist
            print(f"Skipping {folder.name}: prog_index.htm not found.")
            continue

        soup = read_html_file(index_file)

        # 3. Get relevant CSV files based on description
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.endswith('.csv'):
                description = link.find_parent('td').find_next_sibling('td').text

                # Check for target crops in description
                for crop in target_crops:
                    if crop.lower() in description.lower():
                        stage = clean_and_extract_stage(description, crop)

                        csv_path = folder / href
                        if csv_path.exists():
                            print(f"Processing: {crop.lower()} -> {stage}, {href}")
                            process_csv(csv_path, crop, stage)

    print("\nExtraction complete. Total records collected:", len(crop_data))
    print(crop_results)

    output_dir = r"...\cleaned_timeseries"
    export_results_to_csv(crop_results, output_dir)

    """============================================================================="""
    extract_phenology_doy_state_files(r"...\cleaned_timeseries", r"...\Phenology_doy")

    """============================================================================="""

    # Updated biological order dictionary
    crop_orders = {
        "Corn": ["Planted", "Emerged", "Silking", "Dough", "Dented", "Mature", "Harvested"],
        "Soybeans": ["Planted", "Emerged", "Blooming", "Setting", "Dropping", "Harvested"],
        "Spring Wheat": ["Planted", "Emerged", "Headed", "Harvested"]
    }

    # Main Execution
    source_dir = Path(r"...\Phenology_doy")
    output_dir = Path(r"...\Phenology_intervals_day")
    output_dir.mkdir(exist_ok=True)

    # Iterate over all summary files
    for file_path in source_dir.glob("Summary_*.csv"):
        state_name = file_path.stem.replace("Summary_", "")
        intervals_df = calculate_intervals(file_path, crop_orders)

        # Export for this state
        intervals_df.to_csv(output_dir / f"Intervals_{state_name}.csv")
        print(f"Processed intervals for: {state_name}")






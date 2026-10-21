"""
    Builds the region and crop multipliers for the Washington county model areas from the
    WASDA IMPLAN county exports. See README.md in this folder for how to load them.

    From this folder:
        python build_multipliers.py --implan_folder "/path/to/WASDA_Multipliers 2"
            re-reads the IMPLAN .xls exports into implan_crop_sectors.csv (needs xlrd), then builds
        python build_multipliers.py
            builds from the implan_crop_sectors.csv already in this folder
"""

import argparse
import collections
import csv
import json
import os

current_folder = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.dirname(current_folder)

# IMPLAN export name for each county. WA_Counties is the Benton County model - its largest
# industries are Hanford cleanup, PNNL research and Energy Northwest's power plant.
IMPLAN_FILES = {
    "Benton": "WA_Counties",
    "Kittitas": "kittitas2018",
    "Okanogan": "okonagan",
    "Walla Walla": "walla_walla",
    "Yakima": "yakima",
}
IMPLAN_CROP_SECTORS = range(1, 11)  # IMPLAN sectors 1-10 are the crop farming sectors

# model areas with a data folder - regions and crops come from the folder's params.json
AREA_FOLDERS = ["walla_yakima", "WWYAOA2020", "WWYAOA2021", "WWYAOA2022", "WWYAOA2023", "WWYAOA2024", "WWYAOA2025"]

# model areas whose data folders were merged into walla_yakima (commit f0bbede) but are still in the database.
# Regions are from the 2026-10-13 prod dump and the crops match walla_yakima's.
LEGACY_AREAS = {
    "wa_yakima": ["Benton", "Kittitas", "Yakima"],
    "wa_wallawalla": [
        "ARTESIA IRRIGATION DISTRICT NO. 8", "BLALOCK IRRIGATION DISTRICT NO. 3",
        "BLALOCK ORCHARDS IRRIGATION DISTRICT NO. 12", "BRADEN IRRIGATION DISTRICT NO. 20",
        "CONSOLIDATED IRRIGATION DISTRICT NO. 14", "EAST SIDE IRRIGATION DISTRICT NO. 6",
        "GARDENA FARMS DISTRICT NO. 13", "GREEN TANK IRRIGATION DISTRICT NO. 11",
        "HUDSON BAY IRRIGATION DISTRICT NO.", "HYDRO-IRRIGATION DISTRICT NO. 9",
        "MUD CREEK IRRIGATION DISTRICT NO. 7", "ORCHARD IRRIGATION DISTRICT NO. 10",
        "TOUCHET IRRIGATION DISTRICT NO. 16", "TWO RIVERS IRRIGATION DISTRICT NO. 19",
        "WALLA WALLA WATER & POWER DISTRICT NO. 18", "WATER DISTRIBUTION DISTRICT NO.  1",
        "WEST SIDE IRRIGATION DISTRICT NO. 5",
    ],
}

SECTOR_FIELDS = ["county", "implan_file", "implan_code", "implan_sector", "output_total",
                 "value_added_direct", "value_added_total", "employment_direct", "employment_total"]
MULTIPLIER_FIELDS = ["internal_id", "crop_code", "county", "implan_code", "total_revenue",
                     "direct_value_add", "total_value_add", "direct_jobs", "total_jobs"]


def read_csv(path):
    with open(path, 'r', newline='', encoding='utf-8-sig') as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def extract_implan_crop_sectors(implan_folder):
    """
        Reads the crop sectors out of each county's IMPLAN Output, Total Value Added and Employment
        multiplier exports. Output and value added are per $1 of output, employment is jobs per $1M of output.
    """
    import xlrd  # only needed to re-read the IMPLAN exports

    columns = {  # report name: {IMPLAN column: our field}
        "Output Multipliers": {"Total": "output_total"},
        "Total Value Added Multipliers": {"DirectEffects": "value_added_direct", "Total": "value_added_total"},
        "Employment Multipliers": {"DirectEffects": "employment_direct", "Total": "employment_total"},
    }

    rows = []
    for county, implan_file in IMPLAN_FILES.items():
        sectors = {}
        for report, fields in columns.items():
            sheet = xlrd.open_workbook(os.path.join(implan_folder, f"{implan_file} {report}.xls")).sheet_by_index(0)
            header = sheet.row_values(1)  # row 0 is the report title, row 1 the column names
            for row_index in range(2, sheet.nrows):
                code = int(sheet.cell_value(row_index, 0))
                if code in IMPLAN_CROP_SECTORS:
                    sector = sectors.setdefault(code, {"county": county, "implan_file": implan_file, "implan_code": code,
                                                       "implan_sector": sheet.cell_value(row_index, 1)})
                    for column, field in fields.items():
                        sector[field] = sheet.cell_value(row_index, header.index(column))
        rows.extend(sectors[code] for code in IMPLAN_CROP_SECTORS)

    write_csv(os.path.join(current_folder, "implan_crop_sectors.csv"), SECTOR_FIELDS, rows)


def get_area_regions_and_crops(area_folder):
    with open(os.path.join(data_folder, area_folder, "params.json"), 'r') as params_json:
        params = json.load(params_json)

    # the region's internal_id comes from whichever geojson property the field map sends to internal_id
    id_property = [source for source, target in params["region_field_map"] if target == "internal_id"][0]
    with open(os.path.join(data_folder, area_folder, params["regions"]), 'r') as regions_file:
        regions = [json.loads(record)["properties"][id_property] for record in regions_file if record.strip()]

    crops = [row["code"] for row in read_csv(os.path.join(data_folder, area_folder, params["crop_file"]))]
    return regions, crops


def build_multipliers(regions, crops, region_counties, crop_sectors, implan):
    """
        One row per region and crop, using the IMPLAN sector of the crop in the region's county. Jobs
        are converted from per $1M of output to per $1 of revenue, the unit the summary table multiplies by.
    """
    rows = []
    skipped = collections.Counter()  # (county, crop, IMPLAN sector): number of regions without multipliers
    for region in regions:
        county = region_counties[region]
        for crop in crops:
            sector = implan[(county, crop_sectors[crop])]
            if float(sector["output_total"]) == 0:  # IMPLAN has no activity in this sector in the county, so no multipliers
                skipped[(county, crop, sector["implan_sector"])] += 1
                continue

            rows.append({
                "internal_id": region,
                "crop_code": crop,
                "county": county,
                "implan_code": sector["implan_code"],
                "total_revenue": f"{float(sector['output_total']):.12f}",
                "direct_value_add": f"{float(sector['value_added_direct']):.12f}",
                "total_value_add": f"{float(sector['value_added_total']):.12f}",
                "direct_jobs": f"{float(sector['employment_direct']) / 1000000:.12f}",
                "total_jobs": f"{float(sector['employment_total']) / 1000000:.12f}",
            })
    return rows, skipped


def main():
    parser = argparse.ArgumentParser(description="Builds the WASDA multipliers for the Washington county model areas")
    parser.add_argument("--implan_folder", help="folder of IMPLAN .xls exports to re-read into implan_crop_sectors.csv first")
    args = parser.parse_args()

    if args.implan_folder:
        extract_implan_crop_sectors(args.implan_folder)

    region_counties = {row["internal_id"]: row["county"] for row in read_csv(os.path.join(current_folder, "regions_to_counties.csv"))}
    crop_sectors = {row["crop_code"]: row["implan_code"] for row in read_csv(os.path.join(current_folder, "crops_to_implan.csv"))}
    implan = {(row["county"], row["implan_code"]): row for row in read_csv(os.path.join(current_folder, "implan_crop_sectors.csv"))}

    outputs = {}
    for area_folder in AREA_FOLDERS:
        outputs[os.path.join(data_folder, area_folder, "multipliers", "multipliers_by_region_and_crop.csv")] = get_area_regions_and_crops(area_folder)
    _, legacy_crops = get_area_regions_and_crops("walla_yakima")
    for area_name, regions in LEGACY_AREAS.items():
        outputs[os.path.join(current_folder, "legacy_areas", f"{area_name}_multipliers.csv")] = (regions, legacy_crops)

    for output_path, (regions, crops) in outputs.items():
        rows, skipped = build_multipliers(regions, crops, region_counties, crop_sectors, implan)
        write_csv(output_path, MULTIPLIER_FIELDS, rows)
        print(f"{os.path.relpath(output_path, data_folder)}: {len(rows)} rows")
        for (county, crop, implan_sector), count in skipped.items():
            print(f"    no rows for {crop} in {count} {county} region(s) - the {county} IMPLAN model has no {implan_sector} sector")


if __name__ == "__main__":
    main()

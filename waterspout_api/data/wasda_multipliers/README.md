# WASDA multipliers

These are IMPLAN county multipliers for the Washington county model areas. They come from the IMPLAN exports
in the `WASDA_Multipliers 2` folder, one set of four `.xls` reports per county. They replace the old
`walla_yakima/agwa_walla_yakima_okan_mults.csv` and `WWYAOA20XX/district_allocations_mult.csv` files, which had
placeholder 1s, the wrong columns for Okanogan, and acre shares instead of multipliers. Neither file is loaded anymore.

Each region gets its county's multipliers. Each crop gets the IMPLAN sector it belongs to.

## How IMPLAN maps to the app

The summary table multiplies each result's gross revenue by each multiplier, so every value is per $1 of crop revenue.

| `EmploymentMultipliers` field | IMPLAN report | Column | Conversion |
|---|---|---|---|
| `total_revenue` | Output Multipliers | Total | none |
| `direct_value_add` | Total Value Added Multipliers | DirectEffects | none |
| `total_value_add` | Total Value Added Multipliers | Total | none |
| `direct_jobs` | Employment Multipliers | DirectEffects | ÷ 1,000,000 (IMPLAN gives jobs per $1M of output) |
| `total_jobs` | Employment Multipliers | Total | ÷ 1,000,000 |

`Total` is direct + indirect + induced effects, the same as IMPLAN's Type SAM multiplier. The database stores
8 decimal places, so jobs keep about 3 to 4 significant figures.

## Files

- `regions_to_counties.csv`: the county for every region in the Washington county areas. Most come from
  `WWYAOA20XX/WRIA/region_crosswalk.csv`. These seven aren't in that crosswalk, so they were placed by where
  their region geometry is: ATTALIA IRRIGATION DISTRICT NO. 1, Walla Outside Areas, and Walla Walla Irrigated area
  outside irrigation districts (Walla Walla); Home, Zillah, and Yakima Irrigated area outside irrigation districts
  (Yakima); and WATER DISTRIBUTION DISTRICT NO.  1, whose name has a double space here and a single space in the crosswalk.
- `crops_to_implan.csv`: the IMPLAN sector for each crop, kept from the old walla_yakima file.
- `implan_crop_sectors.csv`: IMPLAN crop sectors 1-10 for each county, read from the `.xls` exports.
  Employment is still per $1M here.
- `build_multipliers.py`: builds the files that get loaded (below) from the three CSVs above.
- Output:
  - `walla_yakima/multipliers/multipliers_by_region_and_crop.csv`
  - `WWYAOA2020` to `WWYAOA2025/multipliers/multipliers_by_region_and_crop.csv` (identical; the years share regions and crops)
  - `legacy_areas/wa_yakima_multipliers.csv` and `legacy_areas/wa_wallawalla_multipliers.csv`, for the
    Washington Yakima and Washington Walla Walla areas. Those are still in the database, but their data folders
    were merged into walla_yakima in f0bbede.

To rebuild after changing a mapping, run `python build_multipliers.py` from this folder. To re-read new IMPLAN
exports, run `python build_multipliers.py --implan_folder "/path/to/WASDA_Multipliers 2"`. That needs `pip install xlrd`.

## Decisions to review

- **WA_Counties is treated as Benton County.** The export isn't named after a county. Its largest industries are
  Hanford cleanup (waste remediation), PNNL (scientific research) and Energy Northwest (local government electric
  utilities), and its total employment of 111k is about Benton's. It covers the Benton, FGP and KID regions.
- **Yakima has no Oilseed multipliers.** Yakima's IMPLAN model has no Oilseed farming sector (all zeros), so the
  Yakima regions get no Oilseed row. Those records show the summary table's missing-multipliers warning and count as 0.
  That's about $1.5-2.2M of revenue per run, under 0.1% of the total (Yakima-Wapato, SVID and Yakima Irrigated area
  outside irrigation districts).
  To use a stand-in sector, add it to the build script.
- **Hay/Silage uses Grain farming (sector 2).** This was kept from the old file. IMPLAN's industry bridge puts hay
  farming (NAICS 11194) in All other crop farming (sector 10). To switch, change the row in `crops_to_implan.csv` and rebuild.
- `kittitas2018` is a 2018 IMPLAN model. The other counties' exports don't say which year they are.

## Loading

### A new database

`load_initial_data` (e.g. `--area wwyaok_2024`) loads `multipliers/multipliers_by_region_and_crop.csv` because each
area's `params.json` points to it.

### An existing database (the dev dump or prod)

`replace_multipliers` deletes a model area's multipliers and loads a CSV in their place, in one transaction.
If any row fails, for example a region that isn't in the area, the old multipliers stay. Paths are relative to
`waterspout_api/data`. Nothing needs to rerun: model results don't store multipliers, and the app applies
them each time results are shown. Users see the new values the next time they load the page.

1. Deploy the code with this folder and the `replace_multipliers` command.
2. Check the model area ids. The ones below are from the 2026-10-13 prod dump:

   ```
   python manage.py shell -c "from waterspout_api.models import ModelArea; [print(a.id, a.data_folder, a.name) for a in ModelArea.objects.filter(data_folder__in=['wa_yakima', 'wa_wallawalla', 'walla_yakima', 'WWYAOA2020', 'WWYAOA2021', 'WWYAOA2022', 'WWYAOA2023', 'WWYAOA2024', 'WWYAOA2025']).order_by('id')]"
   ```

3. Load each area. On prod, run these as the service user with the virtualenv's Python:

   ```
   python manage.py replace_multipliers --model_area_id 21 --multipliers_file wasda_multipliers/legacy_areas/wa_yakima_multipliers.csv
   python manage.py replace_multipliers --model_area_id 22 --multipliers_file wasda_multipliers/legacy_areas/wa_wallawalla_multipliers.csv
   python manage.py replace_multipliers --model_area_id 24 --multipliers_file walla_yakima/multipliers/multipliers_by_region_and_crop.csv
   python manage.py replace_multipliers --model_area_id 31 --multipliers_file WWYAOA2020/multipliers/multipliers_by_region_and_crop.csv
   python manage.py replace_multipliers --model_area_id 30 --multipliers_file WWYAOA2021/multipliers/multipliers_by_region_and_crop.csv
   python manage.py replace_multipliers --model_area_id 29 --multipliers_file WWYAOA2022/multipliers/multipliers_by_region_and_crop.csv
   python manage.py replace_multipliers --model_area_id 27 --multipliers_file WWYAOA2023/multipliers/multipliers_by_region_and_crop.csv
   python manage.py replace_multipliers --model_area_id 28 --multipliers_file WWYAOA2024/multipliers/multipliers_by_region_and_crop.csv
   python manage.py replace_multipliers --model_area_id 32 --multipliers_file WWYAOA2025/multipliers/multipliers_by_region_and_crop.csv
   ```

   Each one logs `Deleted N multipliers and loaded M`. M should be 26, 153, 188, then 416 for each WWYAOA year.

The same commands loaded the restored 2026-10-13 dump in dev. After loading, each area's latest base case had
total revenue 1.64 to 1.68 times direct revenue, and total jobs above direct jobs. The only records still missing
multipliers were the Yakima Oilseed ones.

from osgeo import gdal
from code.file_utils import get_base_path
from enum import StrEnum
from pathlib import Path

gdal.UseExceptions()  # recommended: errors raise exceptions instead of just printing ERROR 1:


class OrthomosaicExportFormat(StrEnum):
    GTIFF = "GTiff"
    COG = "COG"


def export_orthomosaic(
        bsq_file_path: str,
        output_file_path: str,
        export_format: OrthomosaicExportFormat):
    """
    Export an band sqeuential envi orthomosaic (*.hdr + *bsq) 
    to the specified format (GTiff or COG).

    bsq_file_path: points to the *.bsq file 
    (make sure *.hdr  is in same directory with same name as *.bsq file)

    output_file_path: path to the output file (with extension .tif or .cog)
    """

    envi_file = gdal.Open(str(bsq_file_path))

    # print(envi_file.GetMetadata("ENVI"))

    options = [
        "-of", export_format.value,
        "-co", "COMPRESS=LZW",
        "-co", "BIGTIFF=IF_NEEDED",
        "-co", "NUM_THREADS=ALL_CPUS",
        "-co", "INTERLEAVE=BAND",
        #"-co", "OVERVIEW_RESAMPLING=NEAREST", # Make sure overviews are nearest neighbor and reflect real values ( no cubic resampling)
    ]

    # TILED is only valid for GTiff; COG is always tiled internally
    if export_format == OrthomosaicExportFormat.GTIFF:
        options += ["-co", "TILED=YES"]

    rsf_str = envi_file.GetMetadataItem("reflectance_scale_factor", "ENVI")  # Important to keep _ !
    if rsf_str:
        # Only add Scale Factor if it is a reflectance orthomosaic (i.e. has the metadata item)
        #options += ["-mo", f"reflectance_scale_factor={rsf_str}"]
        print("dio nothing")

    # First Step Translation
    gdal.Translate(
        output_file_path,
        envi_file,
        options=options,
        callback=gdal.TermProgress_nocb,
    )
    envi_file = None  # close file


def get_all_band_stats(path):
    """Return list of (band_idx, min, max, mean, stddev, nodata) for every band."""
    ds = gdal.Open(path)
    if ds is None:
        raise RuntimeError(f"Could not open {path}")
 
    results = []
    n_bands = ds.RasterCount
    for i in range(1, n_bands + 1):
        band = ds.GetRasterBand(i)
        nodata = band.GetNoDataValue()
        # False = force exact computation, not approximate/estimated
        stats = band.ComputeStatistics(False)
        min_val, max_val, mean_val, std_val = stats
        results.append((i, min_val, max_val, mean_val, std_val, nodata))
 
    ds = None
    return results


def compare(source_path, converted_path, tolerance=1e-6):
    print(f"Source:    {source_path}")
    print(f"Converted: {converted_path}")
    print("Computing exact statistics for all bands (this scans full-resolution "
          "pixel data, so it may take a while for large files)...\n")
 
    src_stats = get_all_band_stats(source_path)
    conv_stats = get_all_band_stats(converted_path)
 
    if len(src_stats) != len(conv_stats):
        print(f"WARNING: band count mismatch! source={len(src_stats)} "
              f"converted={len(conv_stats)}")
 
    mismatches = []
    header = f"{'Band':>5} | {'Src Min':>12} {'Src Max':>12} | {'Conv Min':>12} {'Conv Max':>12} | {'Match?':>6}"
    print(header)
    print("-" * len(header))
 
    for (idx, s_min, s_max, s_mean, s_std, s_nodata), \
        (_, c_min, c_max, c_mean, c_std, c_nodata) in zip(src_stats, conv_stats):
 
        min_ok = abs(s_min - c_min) <= tolerance
        max_ok = abs(s_max - c_max) <= tolerance
        match = min_ok and max_ok
        flag = "OK" if match else "DIFF"
 
        if not match:
            mismatches.append((idx, s_min, s_max, c_min, c_max, s_nodata, c_nodata))
 
        print(f"{idx:>5} | {s_min:>12.4f} {s_max:>12.4f} | {c_min:>12.4f} {c_max:>12.4f} | {flag:>6}")
 
    print("\n" + "=" * 60)
    if not mismatches:
        print(f"All {len(src_stats)} bands match within tolerance ({tolerance}).")
    else:
        print(f"{len(mismatches)} of {len(src_stats)} bands DIFFER:\n")
        for idx, s_min, s_max, c_min, c_max, s_nodata, c_nodata in mismatches:
            print(f"  Band {idx}: source=({s_min:.4f}, {s_max:.4f}) nodata={s_nodata}  "
                  f"converted=({c_min:.4f}, {c_max:.4f}) nodata={c_nodata}")
 
    return mismatches


if __name__ == "__main__":
    print("GDAL version:", gdal.__version__)
    envi_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.bsq"
    tif_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.tif"
    cog_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.cog"
    export_orthomosaic(envi_file_path, tif_file_path, OrthomosaicExportFormat.GTIFF)

for path in [envi_file_path, tif_file_path]:
    ds = gdal.Open(path)
    band = ds.GetRasterBand(1)
    stats = band.ComputeStatistics(False)  # False = exact, not approximate
    
    compare(envi_file_path, tif_file_path, tolerance=1e-6)






from pathlib import Path
import sys

import h5py
import numpy as np
from pyfebio import xplt


sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import FEB_FILE


XPLT_FILE = FEB_FILE.with_suffix(".xplt")
HDF5_FILE = FEB_FILE.with_suffix(".hdf5")
LOG_FILE = FEB_FILE.with_suffix(".log")


def febio_finished_normally():
    """Check the FEBio log file for a normal termination message."""
    if not LOG_FILE.exists():
        return False

    return "N O R M A L   T E R M I N A T I O N" in LOG_FILE.read_text()


def convert_xplt_to_hdf5():
    """Convert FEBio's xplt result file to hdf5 so Python can read it."""
    if not XPLT_FILE.exists():
        raise FileNotFoundError(f"FEBio result file was not found: {XPLT_FILE}")

    if HDF5_FILE.exists():
        HDF5_FILE.unlink()

    xplt.to_hdf5(inputfile=str(XPLT_FILE), outputfile=str(HDF5_FILE))


def read_last_displacement():
    """Read the displacement field from the last time step."""
    with h5py.File(HDF5_FILE, "r") as result_file:
        state_numbers = sorted(result_file["states"].keys(), key=int)
        last_state = state_numbers[-1]
        last_time = result_file[f"states/{last_state}"].attrs["time"][0]

        displacement_group = result_file[f"states/{last_state}/node_data/displacement"]

        all_displacements = []
        for dataset_name in displacement_group:
            all_displacements.append(displacement_group[dataset_name][:])

    displacement = np.vstack(all_displacements)
    displacement_magnitude = np.linalg.norm(displacement, axis=1)

    return last_state, last_time, displacement, displacement_magnitude


def main():
    """Print a small summary of the displacement results."""
    print(f"Reading FEBio result file: {XPLT_FILE}")

    try:
        convert_xplt_to_hdf5()
    except FileNotFoundError as error:
        print("\nResult extraction warning")
        print("- The expected FEBio XPLT result file was not found.")
        print("- This usually means the FEBio model has not been run yet after the latest config change.")
        print(f"- missing file: {XPLT_FILE}")
        print(f"- error: {error}")
        return
    except OSError as error:
        print("\nResult extraction warning")
        print("- FEBio created an XPLT result file, but Python could not convert it to HDF5.")

        if febio_finished_normally():
            print("- The FEBio log still shows normal termination, so the simulation itself finished.")
        else:
            print("- The FEBio log does not show normal termination, so the simulation should be checked.")

        print(f"- conversion error: {error}")
        return

    last_state, last_time, displacement, displacement_magnitude = read_last_displacement()

    print("\nResult summary")
    print(f"- last state: {last_state}")
    print(f"- last time: {last_time}")
    print(f"- number of displacement values: {len(displacement)}")
    print(f"- maximum displacement: {displacement_magnitude.max()}")
    print(f"- average displacement: {displacement_magnitude.mean()}")
    print(f"- minimum x/y/z displacement: {displacement.min(axis=0)}")
    print(f"- maximum x/y/z displacement: {displacement.max(axis=0)}")


if __name__ == "__main__":
    main()

# Build

From the repository root:

    pyinstaller --onedir --console --name=ThermalSync_V3 --collect-all jaraco --collect-all numpy code/tools/thermsync/thermsync.py

The executable lands in `dist/ThermalSync_V3/`. Copy `config.yaml.example`
next to `ThermalSync_V3.exe` as `config.yaml` and adjust `destination_path`
and `target_fps` - the frozen app reads its config from the folder that
contains the executable.

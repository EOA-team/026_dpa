# ThermSync V3

Captures one FLIR A65 frame per second on the DERIS drone and stamps it
with the UTC time of the Applanix NMEA stream, so that ThermoPipe can
georeference each image from the POSPac trajectory. Replaces V1 (May 2026)
and V2 (June 2026); root-cause history of those versions: see the GitHub
issue.

## Modules

| File | Role |
|---|---|
| nmea_reader.py | threaded $--ZDA reader: latest cached time, 2 s receive timeout, reconnects every 2 s |
| thermal_cam.py | camera connection, settings, old-frame discard + fresh fetch, metadata, never-overwrite savers |
| quit_listener.py | background <q>+Enter watcher (RDP-safe) |
| thermsync.py | startup, capture loop, crash-safe teardown |
| config.yaml | destination_path, target_fps (everything else is a code constant) |

## Timestamping (the core design)

V1/V2 fetched once per second and got the OLDEST buffered frame: with
Spinnaker's default OldestFirst handling only 2 frames are stored and the
queue is refilled at the reader's pace, so the fetched frame was always
about (buffers-1) x read period old - 2.0 s at 1 fps, patched in ThermoPipe
with a hand-measured constant.

V3 discards the waiting frames before each fetch, so the fetch can only
return the frame being produced at that instant:

- frame age: <= 33 ms (one camera frame period at the fixed 30 Hz stream)
- time stamp: raw $--ZDA time, at 100 Hz at most ~10 ms old
- total error: expected ~45 ms (frame age up to 33 ms, ZDA age ~10 ms)
  - no patching constant needed

## Behavior in fault cases

| Event | What happens |
|---|---|
| NMEA stream lost | reader detects after 2 s of silence, reconnects every 2 s; frames keep the last time; the never-overwrite rule keeps the first such frame and skips the rest (console warning) until the stream recovers |
| No GPS at start (APX down) | frames saved as thermal_frame_XXXX_UTC_raw.tif; ThermoPipe excludes them (no parseable time) |
| Crash or Ctrl+C | finally-block restores NUC to Automatic and disconnects camera + reader |
| Duplicate filename | writes are skipped with a console warning - recorded data is never destroyed |

## Operation

1. Copy config.yaml.example next to the executable (or script) as
   config.yaml; set destination_path and target_fps.
2. Start the tool; let the camera warm up ~10 min.
3. <s>+Enter starts sampling (NUC locks to Manual), <q>+Enter stops.
4. Per frame the console prints index, UTC time and loop time - the loop
   time should stay around/below the capture period; if it creeps up,
   the disk or metadata reads are the first suspects.

## Output files

- thermal_YYYY-MM-DD_HHMMSS.mmm_UTC_raw.tif - one per frame
- {timestamp}_thermalcam_dynamic_metadata.csv - per frame: sensor,
  housing and shutter temperature, spot reading, NUC mode
- thermalcam_static_metadata.csv - once per session: identity,
  calibration and applied settings

## Before a flight (bench checks)

- Reader: python -m code.tools.thermsync.nmea_reader - advancing UTC
  times within ~1 s, clean Ctrl+C exit
- Full tool: ~2 min run - loop time <= 1 s, timestamps advancing, files
  appearing in destination_path
- Build: see build_command.md (PyInstaller, ThermalSync_V3)

## Known limitations

- No freshness guard (kept simple): during an NMEA outage the first
  stale-stamped frame is kept, the rest are skipped until reconnect.
- The 5 dynamic metadata reads are in the loop budget (~10-50 ms); at
  target_fps higher than ~2 they dominate the loop time.

# Hog Shuttle

A small, boxy spacer shuttle for RimWorld 1.6/1.7, built on Vehicle Framework and VTOL Vehicle. It hovers on
the local map, flies across the world map, and, with Odyssey, flies to orbit and back. Airtight, no weapons
yet, placeholder art.

Requires Harmony, Vehicle Framework, VTOL Vehicle, Vanilla Vehicles Expanded and VVE - Secondary Weapons (for the
door guns). Odyssey, Dubs Bad Hygiene and Combat Extended are optional.

- Design: [DESIGN.md](DESIGN.md)
- In-game checks: [TESTING.md](TESTING.md)
- Placeholder art: `python Source/Art/make_textures.py`
- DLL (sealed cabin): `dotnet build Source/HogShuttle.csproj -c Release` (net48; set `VFDir` in the .csproj
  to your Vehicle Framework folder)

Known issue (not this mod's): on RimWorld 1.7 with Combat Extended, Combat Extended's Vehicle Framework
support fails to load ("Could not load type 'VehiclePartDepth'" in the log), so no Vehicle Framework turret can
fire CE ammo, the Hog's door gun included. On RimWorld 1.6 it works.

License: CC BY-NC-SA 4.0.

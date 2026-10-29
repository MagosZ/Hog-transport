# Hog Shuttle

A small, boxy spacer shuttle for RimWorld 1.6/1.7, built on Vehicle Framework and VTOL Vehicle. It hovers on
the local map, flies across the world map, and, with Odyssey, flies to orbit and back. Airtight, no weapons
yet, placeholder art.

Requires Harmony, Vehicle Framework, VTOL Vehicle and Vanilla Vehicles Expanded. Odyssey is optional.

- Design: [DESIGN.md](DESIGN.md)
- In-game checks: [TESTING.md](TESTING.md)
- Placeholder art: `python Source/Art/make_textures.py`
- DLL (sealed cabin): `dotnet build Source/HogShuttle.csproj -c Release` (net48; set `VFDir` in the .csproj
  to your Vehicle Framework folder)

License: CC BY-NC-SA 4.0.

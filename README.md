# Hog Shuttle

A small, boxy spacer shuttle for RimWorld 1.6/1.7, built on Vehicle Framework and VTOL Vehicle. It hovers on
the local map, flies across the world map, and, with Odyssey, flies to orbit and back. The cabin is sealed and
heated. Upgrades: an auxiliary flight computer, plasteel armour, a cargo outfit, a rear door gun, a roof autocannon,
a front minigun and, with Dubs Bad Hygiene, a chemical toilet.

Requires Harmony, Vehicle Framework, VTOL Vehicle, Vanilla Vehicles Expanded and VVE - Secondary Weapons (for the
door guns and the minigun). Odyssey, Dubs Bad Hygiene and Combat Extended are optional.

- Design: [DESIGN.md](DESIGN.md)
- In-game checks: [TESTING.md](TESTING.md)
- Art: `python Source/Art/make_textures.py` writes the textures, icons and `About/Preview.png`;
  `python Source/Art/components.py` writes the parts and their armour.
- DLL (sealed cabin, orbit fuel, flight computer, front guns, fitted guns' facing, UI pictures):
  `dotnet build Source/HogShuttle.csproj -c Release` (net48; set `VFDir` in the .csproj to your Vehicle Framework
  folder)

License: CC BY-NC-SA 4.0.

# Hog Shuttle: in-game checks

Nothing here has been tested in game yet. Check `Player.log` for errors mentioning `HogShuttle` first.

## Loading
- [ ] No config or XML errors for `HogShuttle`, `HogShuttle_Blueprint` or `HogShuttle_Research`.
- [ ] VTOL Vehicle's "no aircraft found" letter does not appear.
- [ ] The invisible rotor causes no texture or rotor errors.

## Research
- [ ] "hog shuttle" shows in the Vehicles tab at column 3, row 0, linked to aerial vehicles.
- [ ] With Odyssey, it also needs shuttle; without Odyssey it loads and needs only aerial vehicles.
- [ ] Needs a hi-tech research bench with a multi-analyzer.

## Building
- [ ] Blueprint appears in the Vehicles architect tab after the research, costs as in DESIGN.md.
- [ ] Footprint is 4×8 and rotates to 8×4; the placeholder art lines up with it.

## Crew and cargo
- [ ] Pilot seat needed to fly; co-pilot optional; 8 passenger seats.
- [ ] Cargo capacity about 1000 kg.

## Local-map flight (VTOL Vehicle)
- [ ] Take off, fly to a cell, land here, land at a cell, save a landing spot and auto-land.
- [ ] Board nearby and disembark crew.
- [ ] Engine sound plays during flight (VVE rocket engine) and stops after landing.
- [ ] Shadow draws under the shuttle in flight.
- [ ] Out of fuel in flight: emergency landing.

## World map and space (Odyssey)
- [ ] Launch to another surface tile and land.
- [ ] Launch to orbit: a gravship, an orbital site, an asteroid. Land there and come back.
- [ ] Fuel: 600 chemfuel covers a surface-to-orbit trip and back? Tune `fuelCapacity` /
      `fuelConsumptionRate` / `FlightSpeed`.

## Airtight
- [ ] On a space map, pawns inside take no vacuum exposure; the shuttle takes no vacuum damage.
- [ ] Pawns who get out without vacuum gear are exposed (expected).

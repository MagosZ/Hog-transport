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
- [ ] Blueprint appears in the Vehicles architect tab after the research.
- [ ] Cost with Odyssey: 450 steel, 250 plasteel, 10 components, 3 advanced components, 2 shuttle engines.
- [ ] Cost without Odyssey: the same but 9 advanced components and no shuttle engine.
- [ ] Footprint is 4×7 and rotates to 7×4; the placeholder art lines up with it (Draw hitbox).
- [ ] Parked and in flight, at any heading: the top-down view turns with the aircraft; the wings reach one
      cell past the footprint on each side.
- [ ] Painting / patterns: hull and nacelles, cockpit armour + wing stripe, and wings take colours one, two and
      three.

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
- [ ] Range: on a full tank (1200) the launch targeter reaches about 720 tiles over the surface (1.67 fuel
      per tile).
- [ ] Orbit, straight up: the targeter shows about 50 fuel for an orbital target overhead, and about 50 is
      spent; the trip back down costs about 50 plus distance.
- [ ] Orbit to orbit: a hop between two orbital sites costs about 17 fuel per tile (10×), and the tank drains
      that fast in flight.
- [ ] A multi-stop path (surface → orbit → surface) shows and spends 50 for each change.
- [ ] Save mid-flight to orbit, load: no second 50 is taken.
- [ ] Other Vehicle Framework aircraft (VVE, the Hind) keep their old fuel costs.

## Pilot skill and flight computer
- [ ] A pilot with Intellectual 5 or less: the Hog can't move, take off or launch (Vehicle Framework's "not
      enough crew" state). With Intellectual 6+: it flies.
- [ ] Boarding through Vehicle Framework (the gizmo, a caravan) never puts an under-skilled pawn in the pilot
      seat; they take the co-pilot or passenger seats.
- [ ] VTOL Vehicle's "board nearby": check whether it can still seat an under-skilled pilot (the Hog should
      then just stay grounded).
- [ ] The Upgrades tab has "Auxiliary flight computer": 1 advanced component, 200 work, placeholder icon.
- [ ] With it installed, a pilot below Intellectual 6 can fly. If the state doesn't update at once, check
      after the pilot gets out and back in (Vehicle Framework may cache it).
- [ ] Removing it brings the requirement back. Co-pilot and passengers never need the skill.

## Plasteel armour
- [ ] The Upgrades tab has "Plasteel armour": 150 plasteel, 4 components, 6000 work, placeholder icon.
- [ ] Health tab lists all 16 parts (DESIGN.md table). A7 and D7 have no part: check what a hit there does
      (Vehicle Framework may pass it to the nearest part; under CE, the Hind notes such hits do no damage). Shots at the sides (A2-A6, D2-D6) hit the wings, and in
      rows 3-5 also the turbofans (rows 4-5 the rear skids); shots at the tail hit the rear door; the fuel tank sits in the centre (it leaks
      when hit). Damaged turbofans, wings, skids, fuel intake or fuel pumps lower flight speed or
      control; badly damaged turbofans cap both, and they never explode.
- [ ] Installed: every part's armour rises by about 20% in the
      Health tab, and cargo capacity drops from 1000 to 800 kg.
- [ ] Removed: armour and cargo return to normal; half the cost is refunded.
- [ ] Without CE: vanilla ratings (hull 0.50 / 0.90). With CE: CE ratings (hull 22.5 / 11.6) and the
      upgrade adds the CE amounts. No patch errors either way.
- [ ] With CE: check CE's own vehicle compatibility loads (the author's log showed a VehiclesCompat error).

## Cargo outfit
- [ ] The Upgrades tab has "Cargo outfit": no ingredients, 500 work, placeholder icon.
- [ ] Installed: 2 passenger seats (pilot and co-pilot unchanged), cargo 2000 kg; with plasteel armour too,
      1800 kg. Removed: 8 seats and 1000 kg again.
- [ ] Fitting it with more than 2 passengers aboard: see what Vehicle Framework does with the extra pawns.
      Expected: nothing ejects them; they stay until they get out.

## Chemical toilet (with Dubs Bad Hygiene)
- [ ] The Upgrades tab also has "Chemical toilet", with the description and the placeholder icon; without DBH
      only the flight computer is there.
- [ ] Installing it needs 10 steel and 10 neutroamine and takes about as long as building a wooden wall.
- [ ] With it installed, the bladder need of everyone aboard (pilot, co-pilot, passengers) stays full, on the
      map and on the world map; nobody wets themselves on a long trip.
- [ ] Without it, bladder drains as before. Removing it refunds half the cost.
- [ ] Without DBH: no toilet node and no errors.

## Sealed cabin
- [ ] Log: no Harmony error for `MagosZ.HogShuttle`; no error about `HogShuttle.StatPart_SealedCabinVacuum`.
- [ ] In orbit (−75 °C, full vacuum), pawns aboard for a few hours: no hypothermia, no vacuum exposure, no
      vacuum burns.
- [ ] A pawn aboard: vacuum resistance shows 100% with an "Inside a sealed cabin" line in its breakdown.
- [ ] Passengers still get hungry over time (needs keep ticking, as Vehicle Framework intends).
- [ ] Cargo in orbit doesn't freeze; food in the hold rots at room-temperature speed.
- [ ] A pawn who gets out loses the protection again: vacuum resistance back to normal right away or after a
      short delay (the stat is cached), and outside temperature applies.
- [ ] Other Vehicle Framework vehicles (VVE, the Hind) are unchanged: passengers still feel the outside temperature.

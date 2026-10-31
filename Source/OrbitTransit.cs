using System.Collections.Generic;
using System.Runtime.CompilerServices;
using HarmonyLib;
using RimWorld;
using RimWorld.Planet;
using SmashTools;
using SmashTools.Targeting;
using UnityEngine;
using Vehicles;
using Vehicles.World;
using Verse;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: getting into and out of space costs fuel. Vehicle Framework charges by the angle
    /// flown, so a hop to an orbital site straight overhead is nearly free. Each leg whose layer differs from the
    /// one it leaves costs <see cref="transitFuel"/> more, and a leg ending on a space layer costs
    /// <see cref="spaceDistanceFactor"/> times the normal distance cost (vanilla charges gravships by the destination
    /// layer the same way; orbit's rangeDistanceFactor is 20).</summary>
    public class OrbitTransitExtension : DefModExtension
    {
        public float transitFuel = 50f;
        public float spaceDistanceFactor = 20f;

        /// <summary>The fee for changing layer, in step with whatever an upgrade does to the fuel rate (the flight
        /// computer). The distance cost follows the rate by itself.</summary>
        public float TransitFuel(VehiclePawn vehicle)
        {
            CompFueledTravel fuel = vehicle.CompFueledTravel;
            return fuel == null ? transitFuel : transitFuel * fuel.FuelEfficiency / fuel.Props.fuelConsumptionRate;
        }

        /// <summary>Fuel for one leg to <paramref name="to"/>, from Vehicle Framework's distance cost.</summary>
        public float LegCost(VehiclePawn vehicle, float distanceCost, PlanetLayer fromLayer, PlanetTile to)
        {
            if (!to.Valid)
            {
                return distanceCost;
            }
            float cost = to.LayerDef.isSpace ? distanceCost * spaceDistanceFactor : distanceCost;
            if (fromLayer != null && fromLayer != to.Layer)
            {
                cost += TransitFuel(vehicle);
            }
            return cost;
        }
    }

    public static class OrbitTransit
    {
        public static OrbitTransitExtension For(Thing vehicle) => vehicle?.def.GetModExtension<OrbitTransitExtension>();

        public static PlanetLayer LayerOf(PlanetTile tile) => tile.Valid ? tile.Layer : null;
    }

    /// <summary>Single-target estimate (launch checks, "not enough fuel").</summary>
    [HarmonyPatch(typeof(CompVehicleLauncher), nameof(CompVehicleLauncher.FuelNeededToLaunchAtDist),
        new[] { typeof(Vector3), typeof(PlanetTile) })]
    public static class Patch_FuelNeededToLaunchAtDist
    {
        public static void Postfix(CompVehicleLauncher __instance, PlanetTile destination, ref float __result)
        {
            OrbitTransitExtension orbit = OrbitTransit.For(__instance.Vehicle);
            if (orbit != null)
            {
                __result = orbit.LegCost(__instance.Vehicle, __result, OrbitTransit.LayerOf(__instance.Tile), destination);
            }
        }
    }

    /// <summary>The targeter's running total: Vehicle Framework prices the whole path by its total distance, so
    /// redo it leg by leg.</summary>
    [HarmonyPatch(typeof(FuelTargetUpdater), nameof(FuelTargetUpdater.TargeterUpdate))]
    public static class Patch_FuelTargetUpdater_TargeterUpdate
    {
        private static readonly AccessTools.FieldRef<FlightPathTargetUpdater, VehiclePawn> VehicleRef =
            AccessTools.FieldRefAccess<FlightPathTargetUpdater, VehiclePawn>("vehicle");
        private static readonly AccessTools.FieldRef<FlightPathTargetUpdater, ILauncher> LauncherRef =
            AccessTools.FieldRefAccess<FlightPathTargetUpdater, ILauncher>("launcher");
        private static readonly System.Reflection.MethodInfo SetTotalFuelCost =
            AccessTools.PropertySetter(typeof(FuelTargetUpdater), "TotalFuelCost");

        public static void Postfix(FuelTargetUpdater __instance, ref TargetData<GlobalTargetInfo> targetData)
        {
            VehiclePawn vehicle = VehicleRef(__instance);
            OrbitTransitExtension orbit = OrbitTransit.For(vehicle);
            ILauncher launcher = LauncherRef(__instance);
            if (orbit == null || launcher == null || vehicle.CompFueledTravel == null)
            {
                return;
            }
            CompVehicleLauncher comp = vehicle.CompVehicleLauncher;
            Vector3 from = launcher.Origin;
            PlanetLayer fromLayer = OrbitTransit.LayerOf(launcher.Tile);
            float total = 0f;
            List<GlobalTargetInfo> targets = targetData.targets;
            foreach (GlobalTargetInfo target in targets)
            {
                total += Leg(comp, orbit, ref from, ref fromLayer, target.Tile);
            }
            // The leg under the mouse, as Vehicle Framework draws it.
            GlobalTargetInfo mouse = TargetUnderMouse();
            if (mouse.IsValid && targets.Count < comp.launchProtocol.MaxFlightNodes)
            {
                total += Leg(comp, orbit, ref from, ref fromLayer, mouse.Tile);
            }
            SetTotalFuelCost.Invoke(__instance, new object[] { total });
        }

        private static float Leg(CompVehicleLauncher comp, OrbitTransitExtension orbit, ref Vector3 from,
            ref PlanetLayer fromLayer, PlanetTile tile)
        {
            Vector3 to = WorldHelper.GetTilePos(tile);
            float cost = orbit.LegCost(comp.Vehicle, comp.FuelNeededToLaunchAtDist(Ext_Math.SphericalDistance(from, to)),
                fromLayer, tile);
            from = to;
            fromLayer = OrbitTransit.LayerOf(tile);
            return cost;
        }

        // FlightPathTargetUpdater.CurrentTargetUnderMouse
        private static GlobalTargetInfo TargetUnderMouse()
        {
            List<WorldObject> list = GenWorldUI.WorldObjectsUnderMouse(UI.MousePositionOnUI);
            if (!list.NullOrEmpty())
            {
                return list[0];
            }
            PlanetTile tile = GenWorld.MouseTile();
            return tile.Valid ? new GlobalTargetInfo(tile) : GlobalTargetInfo.Invalid;
        }
    }

    /// <summary>Flying a leg that ends in space burns <c>spaceDistanceFactor</c> times the fuel per tick.</summary>
    [HarmonyPatch(typeof(AerialVehicleInFlight), nameof(AerialVehicleInFlight.SpendFuel))]
    public static class Patch_AerialVehicleInFlight_SpendFuel
    {
        public static void Postfix(AerialVehicleInFlight __instance)
        {
            VehiclePawn vehicle = __instance.Vehicle;
            OrbitTransitExtension orbit = OrbitTransit.For(vehicle);
            CompFueledTravel fuel = vehicle?.CompFueledTravel;
            if (orbit == null || fuel == null || __instance.flightPath.Empty ||
                (fuel.FuelCondition & FuelConsumptionCondition.Flying) == 0)
            {
                return;
            }
            PlanetTile to = __instance.flightPath.First.Tile;
            if (to.Valid && to.LayerDef.isSpace && orbit.spaceDistanceFactor > 1f)
            {
                fuel.ConsumeFuel(fuel.ConsumptionRatePerTick * vehicle.CompVehicleLauncher.FuelConsumptionWorldMultiplier *
                    (orbit.spaceDistanceFactor - 1f));
            }
        }
    }

    /// <summary>The transit fee, paid when a leg starts that changes layer. The layer a paid leg heads to counts as
    /// the current one, so re-routing mid-leg doesn't charge twice. Resuming a flight after loading a save
    /// re-plans the path and is never charged.</summary>
    [HarmonyPatch(typeof(AerialVehicleInFlight), "InitializeNextFlight")]
    public static class Patch_AerialVehicleInFlight_InitializeNextFlight
    {
        private class Box
        {
            public PlanetLayer layer;
        }

        private static readonly ConditionalWeakTable<AerialVehicleInFlight, Box> HeadingTo =
            new ConditionalWeakTable<AerialVehicleInFlight, Box>();

        public static bool resuming;

        public static void Postfix(AerialVehicleInFlight __instance)
        {
            VehiclePawn vehicle = __instance.Vehicle;
            OrbitTransitExtension orbit = OrbitTransit.For(vehicle);
            if (orbit == null || __instance.flightPath.Empty)
            {
                return;
            }
            Box heading = HeadingTo.GetOrCreateValue(__instance);
            PlanetLayer fromLayer = heading.layer ?? OrbitTransit.LayerOf(__instance.Tile);
            PlanetLayer toLayer = OrbitTransit.LayerOf(__instance.flightPath.First.Tile);
            heading.layer = toLayer;
            if (resuming || fromLayer == null || toLayer == null || fromLayer == toLayer)
            {
                return;
            }
            vehicle.CompFueledTravel?.ConsumeFuel(orbit.TransitFuel(vehicle));
        }
    }

    [HarmonyPatch(typeof(AerialVehicleInFlight), "ResumePathPostLoad")]
    public static class Patch_AerialVehicleInFlight_ResumePathPostLoad
    {
        public static void Prefix() => Patch_AerialVehicleInFlight_InitializeNextFlight.resuming = true;

        public static void Finalizer() => Patch_AerialVehicleInFlight_InitializeNextFlight.resuming = false;
    }
}

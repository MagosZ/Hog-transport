using System;
using System.Reflection;
using HarmonyLib;
using Vehicles;
using Verse;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: what an upgrade does to the fuel rate also applies to the fuel VTOL Vehicle burns while
    /// airborne on the map (the flight computer).</summary>
    public class HoverFuelFollowsRateExtension : DefModExtension
    {
    }

    /// <summary>VTOL Vehicle burns AircraftProperties.fuelConsumptionPerTick while airborne on the map, from the def, so it
    /// can't be changed per vehicle. Vehicle Framework's fuel rate doesn't touch it. So the saved part is handed back,
    /// every 250 ticks.</summary>
    [HarmonyPatch(typeof(VehiclePawn), nameof(VehiclePawn.TickRare))]
    public static class Patch_VehiclePawn_TickRare_HoverFuel
    {
        private const int Interval = 250;

        private static readonly Type PawnType = AccessTools.TypeByName("VTOLVehicle.VtolVehiclePawn");
        private static readonly Type PropsType = AccessTools.TypeByName("VTOLVehicle.AircraftProperties");
        private static readonly MethodInfo IsAirborne = AccessTools.PropertyGetter(PawnType, "IsAirborne");
        private static readonly FieldInfo BurnPerTick = AccessTools.Field(PropsType, "fuelConsumptionPerTick");
        private static readonly AccessTools.FieldRef<CompFueledTravel, float> FuelRef =
            AccessTools.FieldRefAccess<CompFueledTravel, float>("fuel");

        public static void Postfix(VehiclePawn __instance)
        {
            if (!__instance.Spawned || __instance.def.GetModExtension<HoverFuelFollowsRateExtension>() == null ||
                !PawnType.IsInstanceOfType(__instance) || !(bool)IsAirborne.Invoke(__instance, null))
            {
                return;
            }
            CompFueledTravel fuel = __instance.CompFueledTravel;
            if (fuel == null || fuel.EmptyTank)
            {
                return;
            }
            float saving = 1f - fuel.FuelEfficiency / fuel.Props.fuelConsumptionRate;
            if (saving <= 0f)
            {
                return;
            }
            foreach (DefModExtension extension in __instance.def.modExtensions)
            {
                if (PropsType.IsInstanceOfType(extension))
                {
                    float burned = (float)BurnPerTick.GetValue(extension) * Interval;
                    FuelRef(fuel) = Math.Min(fuel.Fuel + burned * saving, fuel.FuelCapacity);
                    return;
                }
            }
        }
    }
}

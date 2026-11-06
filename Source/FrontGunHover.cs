using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using RimWorld;
using Vehicles;
using Verse;
using Verse.AI;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: the gun with key <see cref="turret"/> drives: VTOL Vehicle's combat hover answers only to it
    /// and holds the nose on its target. Other guns never turn the shuttle.</summary>
    public class SteadyFrontGunExtension : DefModExtension
    {
        public string turret;

        public VehicleTurret Driver(VehiclePawn vehicle)
        {
            IReadOnlyList<VehicleTurret> fitted = vehicle.CompVehicleTurrets?.Turrets;
            if (fitted != null)
            {
                foreach (VehicleTurret candidate in fitted)
                {
                    if (candidate.key == turret)
                    {
                        return candidate;
                    }
                }
            }
            return null;
        }
    }

    /// <summary>VTOL Vehicle's flight controller, by reflection: the build has no reference to VTOLVehicle.dll. Method and
    /// field names as the Hind Gunship's source uses them.</summary>
    internal static class Vtol
    {
        public static readonly Type Controller = AccessTools.TypeByName("VTOLVehicle.VtolFlightController");
        public static readonly FieldInfo ControllerVehicle = Controller == null ? null : AccessTools.Field(Controller, "vehicle");

        public static MethodInfo Method(string name) => Controller == null ? null : AccessTools.Method(Controller, name);

        public static VehiclePawn VehicleOf(object controller) => ControllerVehicle?.GetValue(controller) as VehiclePawn;
    }

    /// <summary>VTOL Vehicle stops applying the combat facing once the hovering aircraft has lined up, and hands the nose back
    /// to the last move order's facing. The nose wanders off, comes back, and the gun loses its target over and over. So
    /// the combat facing stays applied.</summary>
    [HarmonyPatch]
    public static class Patch_VtolFlightController_ShouldApplyCombatFacing
    {
        public static bool Prepare() => TargetMethod() != null && Vtol.ControllerVehicle != null;

        public static MethodBase TargetMethod() => Vtol.Method("ShouldApplyCombatDirectionalHoverFacing");

        public static void Postfix(object __instance, ref bool __result)
        {
            if (!__result && Vtol.VehicleOf(__instance)?.def.GetModExtension<SteadyFrontGunExtension>() != null)
            {
                __result = true;
            }
        }
    }

    /// <summary>VTOL Vehicle's combat hover turns the nose to the best target of any auto-targeting gun, so a door gun's
    /// target behind the shuttle, or the autocannon's, would swing the nose. Only the minigun's target counts, and with no
    /// minigun, or one that can't fire, the nose stays free.</summary>
    [HarmonyPatch]
    public static class Patch_VtolFlightController_BestAutoTarget
    {
        // VTOL Vehicle's own scan flag for these searches, which looks past the gun's arc.
        private const TargetScanFlags HoverScan = (TargetScanFlags)256;

        private static readonly MethodInfo IsValid = Vtol.Method("IsValidCombatDirectionalHoverTarget");

        public static bool Prepare() => TargetMethod() != null && Vtol.ControllerVehicle != null && IsValid != null;

        public static MethodBase TargetMethod() => Vtol.Method("BestVehicleTurretAutoTarget");

        public static void Postfix(object __instance, ref Thing __result)
        {
            VehiclePawn vehicle = Vtol.VehicleOf(__instance);
            SteadyFrontGunExtension steady = vehicle?.def.GetModExtension<SteadyFrontGunExtension>();
            if (steady == null)
            {
                return;
            }
            __result = null;
            VehicleTurret driver = steady.Driver(vehicle);
            if (driver != null && driver.AutoTarget && !driver.TurretDisabled &&
                driver.TryGetTarget(out LocalTargetInfo found, HoverScan) && found.HasThing &&
                (bool)IsValid.Invoke(__instance, new object[] { found.Thing, true }))
            {
                __result = found.Thing;
            }
        }
    }
}

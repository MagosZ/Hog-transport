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

        public static readonly Type Turret = AccessTools.TypeByName("VTOLVehicle.VtolVehicleTurret");
        public static readonly MethodInfo IsValidHoverTarget =
            Controller == null ? null : AccessTools.Method(Controller, "IsValidCombatDirectionalHoverTarget");

        public static readonly MethodInfo LastRequest =
            Turret == null ? null : AccessTools.PropertyGetter(Turret, "LastVtolTargetRequest");
        public static readonly MethodInfo FacingFor =
            Turret == null ? null : AccessTools.Method(Turret, "TryGetVehicleFacingForTarget");

        public static MethodInfo Method(string name) => Controller == null ? null : AccessTools.Method(Controller, name);

        public static VehiclePawn VehicleOf(object controller) => ControllerVehicle?.GetValue(controller) as VehiclePawn;

        public static VehicleTurret DriverOf(object controller)
        {
            VehiclePawn vehicle = VehicleOf(controller);
            return vehicle?.def.GetModExtension<SteadyFrontGunExtension>()?.Driver(vehicle);
        }

        public static Thing Request(VehicleTurret turret) =>
            LastRequest != null && Turret.IsInstanceOfType(turret) ? ((LocalTargetInfo)LastRequest.Invoke(turret, null)).Thing : null;

        /// <summary>What the driving gun is after: its own target, else the one asked for by hand.</summary>
        public static Thing Aim(object controller, VehicleTurret driver)
        {
            if (driver == null || driver.TurretDisabled || IsValidHoverTarget == null)
            {
                return null;
            }
            Thing own = driver.targetInfo.Thing;
            if (Usable(controller, driver, own))
            {
                return own;
            }
            Thing asked = Request(driver);
            return Usable(controller, driver, asked) ? asked : null;
        }

        private static bool Usable(object controller, VehicleTurret turret, Thing thing) =>
            thing != null && thing.Spawned && !thing.Destroyed &&
            (bool)IsValidHoverTarget.Invoke(controller, new object[] { thing, true }) &&
            turret.InRange(new LocalTargetInfo(thing));
    }

    /// <summary>VTOL Vehicle's combat facing only follows a gun's current target. A fixed gun can't take a target outside its
    /// narrow arc, so a target given by hand off the nose stays a request (LastVtolTargetRequest) and the nose never turns
    /// to it. So the minigun's own target comes first, then the one asked for by hand, and the nose turns to whichever it
    /// is. With neither, VTOL picks as usual.</summary>
    [HarmonyPatch]
    public static class Patch_VtolFlightController_CombatFacing
    {
        public static bool Prepare() => TargetMethod() != null && Vtol.ControllerVehicle != null &&
            Vtol.IsValidHoverTarget != null && Vtol.LastRequest != null && Vtol.FacingFor != null;

        public static MethodBase TargetMethod() => Vtol.Method("TryGetTurretCombatFacing");

        public static bool Prefix(object __instance, ref bool __result, ref float facingAngle, ref Thing target)
        {
            VehicleTurret driver = Vtol.DriverOf(__instance);
            Thing aim = Vtol.Aim(__instance, driver);
            if (aim == null)
            {
                return true;
            }
            object[] args = { aim.DrawPos, 0f };
            if (!(bool)Vtol.FacingFor.Invoke(driver, args))
            {
                return true;
            }
            facingAngle = (float)args[1];
            target = aim;
            __result = true;
            return false;
        }
    }

    /// <summary>VTOL Vehicle stops applying the combat facing once the hovering aircraft has lined up, and hands the nose back
    /// to the last move order's facing. The nose wanders off, comes back, and the gun loses its target over and over. So
    /// the combat facing stays applied while the minigun has a target.</summary>
    [HarmonyPatch]
    public static class Patch_VtolFlightController_ShouldApplyCombatFacing
    {
        public static bool Prepare() => TargetMethod() != null && Vtol.ControllerVehicle != null;

        public static MethodBase TargetMethod() => Vtol.Method("ShouldApplyCombatDirectionalHoverFacing");

        public static void Postfix(object __instance, ref bool __result)
        {
            if (__result)
            {
                return;
            }
            // Only while the minigun is after something, so VTOL's own steering for a target given by hand isn't shut out.
            if (Vtol.Aim(__instance, Vtol.DriverOf(__instance)) != null)
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

        private static readonly MethodInfo IsValid = Vtol.IsValidHoverTarget;

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

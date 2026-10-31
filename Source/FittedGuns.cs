using System.Reflection;
using HarmonyLib;
using UnityEngine;
using Vehicles;
using Verse;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: a gun fitted by an upgrade starts out facing its default direction, relative to the
    /// aircraft.</summary>
    public class FittedGunsAlignExtension : DefModExtension
    {
    }

    /// <summary>Vehicle Framework treats a new turret's default angle as a world angle (0 = north), and VTOL Vehicle only
    /// swings an idle gun back once it's crewed, so a gun fitted on a Hog parked facing east would sit pointing north until
    /// someone boarded. Guns loaded from a save don't come through here with an upgrade key, so they keep their rotation.</summary>
    [HarmonyPatch(typeof(CompVehicleTurrets), nameof(CompVehicleTurrets.AddTurret))]
    public static class Patch_CompVehicleTurrets_AddTurret
    {
        private static readonly FieldInfo FacingAngle =
            AccessTools.Field(AccessTools.TypeByName("VTOLVehicle.VtolVehiclePawn"), "FacingAngle");

        public static void Postfix(CompVehicleTurrets __instance, VehicleTurret turret, string upgradeKey)
        {
            VehiclePawn vehicle = __instance.Vehicle;
            if (upgradeKey == null || turret.attachedTo != null ||
                vehicle?.def.GetModExtension<FittedGunsAlignExtension>() == null)
            {
                return;
            }
            float heading = FacingAngle?.DeclaringType.IsInstanceOfType(vehicle) == true
                ? (float)FacingAngle.GetValue(vehicle)
                : vehicle.Rotation.AsAngle;
            float angle = Mathf.Repeat(heading + turret.defaultAngleRotated, 360f);
            turret.TurretRotation = angle;
            turret.TurretRotationTargeted = angle;
        }
    }
}

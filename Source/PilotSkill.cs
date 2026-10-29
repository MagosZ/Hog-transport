using HarmonyLib;
using RimWorld;
using Vehicles;
using Verse;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: a pawn only counts as operating <see cref="role"/> with at least
    /// <see cref="minLevel"/> in <see cref="skill"/>, unless the upgrade node <see cref="waivedByUpgradeNode"/> is
    /// installed.</summary>
    public class PilotSkillExtension : DefModExtension
    {
        public string role = "Pilot";
        public SkillDef skill;
        public int minLevel;
        public string waivedByUpgradeNode;

        public bool Waived(VehiclePawn vehicle)
        {
            if (waivedByUpgradeNode.NullOrEmpty())
            {
                return false;
            }
            CompUpgradeTree tree = vehicle.CompUpgradeTree;
            UpgradeNode node = tree?.Props.def.GetNode(waivedByUpgradeNode);
            return node != null && tree.NodeUnlocked(node);
        }
    }

    /// <summary>Vehicle Framework's per-seat check. It decides whether the seat is crewed (RoleFulfilled, so whether
    /// the vehicle can move at all) and which seat boarding pawns are given.</summary>
    [HarmonyPatch(typeof(VehicleRoleHandler), nameof(VehicleRoleHandler.CanOperateRole), new[] { typeof(Pawn) })]
    public static class Patch_VehicleRoleHandler_CanOperateRole
    {
        public static void Postfix(VehicleRoleHandler __instance, Pawn pawn, ref bool __result)
        {
            if (!__result || __instance.vehicle == null)
            {
                return;
            }
            PilotSkillExtension pilot = __instance.vehicle.def.GetModExtension<PilotSkillExtension>();
            if (pilot?.skill == null || __instance.role?.key != pilot.role || pilot.Waived(__instance.vehicle))
            {
                return;
            }
            SkillRecord record = pawn.skills?.GetSkill(pilot.skill);
            if (record == null || record.TotallyDisabled || record.Level < pilot.minLevel)
            {
                __result = false;
            }
        }
    }
}

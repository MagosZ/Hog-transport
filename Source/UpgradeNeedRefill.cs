using HarmonyLib;
using RimWorld;
using Vehicles;
using Verse;

namespace HogShuttle
{
    /// <summary>On a VehicleDef: while <see cref="upgradeNode"/> is installed, <see cref="need"/> of everyone aboard
    /// is kept full (the chemical toilet and Dubs Bad Hygiene's bladder).</summary>
    public class UpgradeNeedRefillExtension : DefModExtension
    {
        public string upgradeNode;
        public NeedDef need;
    }

    /// <summary>Vehicle Framework calls TickRare every 250 ticks from the vehicle's own tick, on the map and in
    /// flight.</summary>
    [HarmonyPatch(typeof(VehiclePawn), nameof(VehiclePawn.TickRare))]
    public static class Patch_VehiclePawn_TickRare
    {
        public static void Postfix(VehiclePawn __instance)
        {
            UpgradeNeedRefillExtension refill = __instance.def.GetModExtension<UpgradeNeedRefillExtension>();
            if (refill?.need == null)
            {
                return;
            }
            CompUpgradeTree tree = __instance.CompUpgradeTree;
            UpgradeNode node = tree?.Props.def.GetNode(refill.upgradeNode);
            if (node == null || !tree.NodeUnlocked(node))
            {
                return;
            }
            foreach (Pawn pawn in __instance.AllPawnsAboard)
            {
                Need need = pawn.needs?.TryGetNeed(refill.need);
                if (need != null)
                {
                    need.CurLevel = need.MaxLevel;
                }
            }
        }
    }
}

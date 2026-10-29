using RimWorld;
using Verse;

namespace HogShuttle
{
    /// <summary>On Odyssey's VacuumResistance: a pawn aboard a sealed cabin is fully resistant. Vacuum belongs to the
    /// cell under the vehicle, so it can't be cleared for the cabin alone; full resistance has the same effect
    /// (vacuum exposure and vacuum burns scale with 1 - resistance).</summary>
    public class StatPart_SealedCabinVacuum : StatPart
    {
        public override void TransformValue(StatRequest req, ref float val)
        {
            if (req.Thing is Pawn pawn && SealedCabin.HolderOf(pawn) != null)
            {
                val = 1f;
            }
        }

        public override string ExplanationPart(StatRequest req)
        {
            if (req.Thing is Pawn pawn && SealedCabin.HolderOf(pawn) != null)
            {
                return "HogShuttle_SealedCabin".Translate() + ": " + 1f.ToStringPercent();
            }
            return null;
        }
    }
}

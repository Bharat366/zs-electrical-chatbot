"""
MCP Server for Zs Electrical Chatbot
Exposes the backend endpoints as MCP tools so they appear in MCP Inspector.
"""
import re
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Zs Electrical Agent")

MULT = {"B": 5, "C": 10, "D": 20}

# ─── Tool 1: Calculate Zs ───────────────────────────────────────────────────
@mcp.tool()
def calculate_zs(
    earth_pits: list[float],
    earth_grid: float,
    r1_phase: float = 0.0,
    r2_earth: float = 0.0,
    mcb_type: str = "",
    mcb_rating_amps: float = 0.0,
    u0_volts: float = 230.0
) -> dict:
    """
    Calculate earth fault loop impedance Zs = Ze + (R1 + R2).
    Combines earth pits and grid in parallel to get Ze.
    Checks compliance: Zs <= (2/3) * (U0 / Ia) for the selected MCB.

    Args:
        earth_pits: List of individual earth pit resistances in ohms (e.g. [4.2, 5.1, 3.8])
        earth_grid: Earth grid resistance in ohms (e.g. 0.9)
        r1_phase: Phase conductor resistance in ohms (default 0)
        r2_earth: Earth/protective conductor resistance in ohms (default 0)
        mcb_type: MCB curve type - 'B', 'C', or 'D'
        mcb_rating_amps: MCB current rating in amps (e.g. 32)
        u0_volts: Line-to-earth voltage, default 230V
    """
    electrodes = [x for x in earth_pits if x > 0]
    if earth_grid > 0:
        electrodes.append(earth_grid)

    if not electrodes:
        return {"error": "Provide at least one earth pit or grid resistance."}

    ze = 1.0 / sum(1.0 / v for v in electrodes)
    zs = ze + r1_phase + r2_earth

    pit_flags = [f"Pit {i+1} ({v} ohm) >= 5 ohm EXCEEDS STANDARD" for i, v in enumerate(earth_pits) if v >= 5]
    grid_flag = f"Grid ({earth_grid} ohm) >= 1 ohm EXCEEDS STANDARD" if earth_grid >= 1 else ""

    result = {
        "Ze_ohm": round(ze, 4),
        "Zs_ohm": round(zs, 4),
        "R1_ohm": r1_phase,
        "R2_ohm": r2_earth,
        "electrodes_combined": len(electrodes),
        "pit_warnings": pit_flags,
        "grid_warning": grid_flag if grid_flag else "Grid OK",
    }

    if mcb_type.upper() in MULT and mcb_rating_amps > 0:
        ia = MULT[mcb_type.upper()] * mcb_rating_amps
        limit = (2.0 / 3.0) * (u0_volts / ia)
        ok = zs <= limit
        result.update({
            "MCB_type": mcb_type.upper(),
            "MCB_rating_A": mcb_rating_amps,
            "Ia_trip_current_A": ia,
            "max_Zs_limit_ohm": round(limit, 4),
            "verdict": "PASS" if ok else "FAIL",
            "margin_ohm": round(limit - zs, 4),
        })
    else:
        result["verdict"] = "No MCB specified - cannot check compliance"

    return result


# ─── Tool 2: Check single earth pit ─────────────────────────────────────────
@mcp.tool()
def check_earth_pit(resistance_ohm: float) -> dict:
    """
    Check whether a single earth pit resistance meets the standard (< 5 ohm).

    Args:
        resistance_ohm: Measured resistance of the earth pit in ohms
    """
    return {
        "resistance_ohm": resistance_ohm,
        "standard_limit_ohm": 5.0,
        "status": "PASS - Within limit" if resistance_ohm < 5 else "FAIL - Exceeds 5 ohm limit",
        "recommendation": "OK" if resistance_ohm < 5 else "Drive deeper rod, add parallel electrode, or treat soil."
    }


# ─── Tool 3: Check earth grid ────────────────────────────────────────────────
@mcp.tool()
def check_earth_grid(resistance_ohm: float) -> dict:
    """
    Check whether an earth grid resistance meets the standard (< 1 ohm).

    Args:
        resistance_ohm: Measured resistance of the earth grid in ohms
    """
    return {
        "resistance_ohm": resistance_ohm,
        "standard_limit_ohm": 1.0,
        "status": "PASS - Within limit" if resistance_ohm < 1 else "FAIL - Exceeds 1 ohm limit",
        "recommendation": "OK" if resistance_ohm < 1 else "Add more grid conductors or bonding electrodes."
    }


# ─── Tool 4: MCB compliance limit ───────────────────────────────────────────
@mcp.tool()
def mcb_compliance_limit(mcb_type: str, rating_amps: float, u0_volts: float = 230.0) -> dict:
    """
    Calculate the maximum allowed Zs for an MCB using formula: max_Zs = (2/3) * (U0 / Ia).

    Args:
        mcb_type: Type B, C, or D
        rating_amps: MCB rated current in amps (e.g. 16, 32, 63)
        u0_volts: Line-to-earth voltage, default 230V
    """
    t = mcb_type.strip().upper()
    if t not in MULT:
        return {"error": "MCB type must be B, C, or D"}
    ia = MULT[t] * rating_amps
    limit = (2.0 / 3.0) * (u0_volts / ia)
    return {
        "MCB_type": t,
        "rating_A": rating_amps,
        "multiplier": MULT[t],
        "Ia_trip_current_A": ia,
        "U0_volts": u0_volts,
        "max_Zs_ohm": round(limit, 4),
        "formula": f"(2/3) × ({u0_volts}/{ia}) = {round(limit,4)} ohm"
    }


# ─── Tool 5: Parallel resistance ────────────────────────────────────────────
@mcp.tool()
def parallel_resistance(resistances: list[float]) -> dict:
    """
    Combine any number of resistances in parallel (used for earth electrodes).
    Formula: 1/R_total = 1/R1 + 1/R2 + ...

    Args:
        resistances: List of resistance values in ohms
    """
    if not resistances or any(r <= 0 for r in resistances):
        return {"error": "All resistance values must be positive numbers."}
    total = 1.0 / sum(1.0 / r for r in resistances)
    return {
        "input_resistances_ohm": resistances,
        "parallel_total_ohm": round(total, 4),
        "note": "Combined Ze is always lower than the smallest individual electrode."
    }


if __name__ == "__main__":
    mcp.run()

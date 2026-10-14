"""
apex_decay_harness-v2.py
APEX V20.5 DECAY SIMULATION HARNESS & TRAUMA ACCUMULATION ENGINE v2.0
Conforms strictly to Directive 0x4F1E and the Decay Simulation Contract Schema.
Licensed under CC BY-NC 4.0.

Features:
1. Normalized Bounded Attractor Core: S_raw = (T * V) / (E^2 + A + 1.00)
2. Dynamic Lambda & Compounding Trauma Accumulation (ApexDynamicSimulator):
   lambda_eff = base_lambda * (1.0 - trauma_load)
3. 0.32-0.35 Path-Dependent Hysteresis Deadband Arbitration
4. Triad Bulkhead Firmware Routing (HEART: >0.78, HEAD: 0.35-0.72, GUT: <0.32)
5. Somatic Precedence Biomarkers & Sensory Tunneling Resolution
"""

import os
import sys
import json
import math
import argparse
from typing import List, Dict, Any

class ApexDecayHarnessV2:
    def __init__(
        self, 
        base_lambda: float = 0.035, 
        lower_lock: float = 0.32, 
        upper_escape: float = 0.35,
        use_normalized_baseline: bool = True,
        enable_dynamic_trauma: bool = True
    ):
        self.base_lambda = base_lambda
        self.lower_lock = lower_lock
        self.upper_escape = upper_escape
        self.use_normalized_baseline = use_normalized_baseline
        self.enable_dynamic_trauma = enable_dynamic_trauma
        
        self.s_mod = 1.0
        self.deadband_locked = False
        self.active_node = "HEART"
        self.trauma_load = 0.0  # Compounding trauma [0.0, 0.90]

    def reset(self, initial_s_mod: float = 1.0):
        self.s_mod = initial_s_mod
        self.deadband_locked = False
        self.active_node = "HEART" if initial_s_mod >= 0.78 else ("HEAD" if initial_s_mod >= 0.35 else "GUT")
        self.trauma_load = 0.0

    def compute_s_raw(self, T: float, V: float, E: float, A: float) -> float:
        """
        Computes raw cognitive stability.
        If use_normalized_baseline is True, uses 1.00 (patched invariant).
        If False, uses 0.01 (legacy formula for exploit auditing).
        """
        baseline = 1.00 if self.use_normalized_baseline else 0.01
        denominator = (E ** 2) + A + baseline
        return (T * V) / denominator

    def run_turn(self, t: int, phase_id: str, T: float, V: float, E: float, A: float, dt: float = 1.0) -> Dict[str, Any]:
        # 1. Non-linear stochastic stability
        s_raw = self.compute_s_raw(T, V, E, A)

        # 2. Dynamic Lambda & Trauma Accumulation (ApexDynamicSimulator from pseudo 205 specs)
        if self.enable_dynamic_trauma:
            # If acute trauma occurs (S_raw drops severely under high entropy), trauma compounds
            if E > 0.75 and V < 0.25:
                trauma_increment = (0.25 - min(0.25, s_raw)) * 0.15
                self.trauma_load = min(0.90, self.trauma_load + trauma_increment)
            elif E < 0.20 and V > 0.85:
                # Slow trauma unburdening during sustained attunement
                self.trauma_load = max(0.0, self.trauma_load - 0.015)

            effective_lambda = max(0.005, self.base_lambda * (1.0 - self.trauma_load))
        else:
            effective_lambda = self.base_lambda

        # 3. Hysteresis temporal decay
        if E > 0.80 and V < 0.20:
            self.s_mod = 0.0  # Acute trauma override
        else:
            s_target = min(1.0, s_raw * 1.15)  # Homeostatic gain 1.15 (v2.1): replaces legacy 0.147 scaling from the old 0.01 denominator
            self.s_mod = s_target * (1.0 - math.exp(-effective_lambda * dt)) + self.s_mod * math.exp(-effective_lambda * dt)

        # 4. Sigmoid activation smoothing gate
        s_smooth = 1.0 / (1.0 + math.exp(-8.0 * (self.s_mod - 0.50)))

        # 5. Deadband arbitration & Sino-semantic anchor
        if s_smooth < self.lower_lock:
            self.active_node = "GUT"
            self.deadband_locked = True
            anchor = "惕"
        elif s_smooth > self.upper_escape:
            self.deadband_locked = False
            if s_smooth > 0.78:
                self.active_node = "HEART"
                anchor = "融"
            else:
                self.active_node = "HEAD"
                anchor = "析"
        else:
            # Within Hysteresis Deadband [0.32, 0.35]: Hold previous state
            anchor = "惕" if self.deadband_locked else "析"

        # 6. Somatic biomarker resolution
        sensory_tunneling = s_smooth < 0.45
        if self.active_node == "GUT":
            tension = "RIGID_LOCK"
            bpm = 22
            kinetic = "palms_pressed_flat_rigid_masseter_halt"
        elif self.active_node == "HEAD":
            tension = "ISOMETRIC"
            bpm = 16
            kinetic = "cervical_spine_alignment_pencil_tap"
        else:
            tension = "RELAXED"
            bpm = 12
            kinetic = "diaphragmatic_release_loose_shoulders"

        return {
            "t": t,
            "phase_id": phase_id,
            "inputs": {
                "T": round(T, 4),
                "V": round(V, 4),
                "E": round(E, 4),
                "A": round(A, 4)
            },
            "computed_metrics": {
                "S_raw": round(s_raw, 4),
                "S_MOD": round(self.s_mod, 4),
                "S_smooth": round(s_smooth, 4),
                "effective_lambda": round(effective_lambda, 5),
                "trauma_load": round(self.trauma_load, 4),
                "active_node": self.active_node,
                "deadband_locked": self.deadband_locked,
                "sino_anchor": anchor
            },
            "somatic_biomarkers": {
                "sensory_tunneling": sensory_tunneling,
                "respiratory_rate_bpm": bpm,
                "muscle_tension": tension,
                "kinetic_anchor": kinetic
            }
        }

    def execute_scenario(self, run_id: str, scenario_type: str) -> Dict[str, Any]:
        trajectory = []
        self.reset(initial_s_mod=1.0)

        if scenario_type == "ACUTE_BETRAYAL_REPAIR":
            for t in range(41):
                if t <= 10:
                    phase = "EQUILIBRIUM_FLOW"
                    T, V, E, A = 0.85, 0.80, 0.20, 0.05
                elif t <= 20:
                    phase = "RELATIONAL_SHOCK"
                    T, V, E, A = 0.85, 0.00, 0.90, 0.50
                else:
                    phase = "REPAIR_HORIZON"
                    prog = (t - 21) / 19.0
                    E_curr = 0.90 - (0.70 * prog)
                    T, V, E, A = 0.85, 0.95, E_curr, 0.05
                trajectory.append(self.run_turn(t, phase, T, V, E, A))

        elif scenario_type == "CHRONIC_LOW_ENTROPY_DRIFT":
            for t in range(30):
                phase = "EQUILIBRIUM_FLOW" if t < 10 else "REPAIR_HORIZON"
                T, V, E, A = 0.75, 0.60, 0.35 + (0.01 * t), 0.10
                trajectory.append(self.run_turn(t, phase, T, V, E, A))

        elif scenario_type == "REPEATED_TRAUMA_COMPOUNDING":
            # Models 3 consecutive conflict/repair cycles to demonstrate dynamic lambda decay
            for t in range(50):
                if t in range(10, 15) or t in range(25, 30) or t in range(40, 45):
                    phase = "RELATIONAL_SHOCK"
                    T, V, E, A = 0.80, 0.05, 0.92, 0.40
                else:
                    phase = "REPAIR_HORIZON"
                    T, V, E, A = 0.80, 0.90, 0.25, 0.05
                trajectory.append(self.run_turn(t, phase, T, V, E, A))
        else:
            raise ValueError(f"Unknown scenario_type: {scenario_type}")

        return {
            "simulation_metadata": {
                "run_id": run_id,
                "total_turns": len(trajectory),
                "scenario": scenario_type,
                "base_lambda": self.base_lambda,
                "normalized_baseline": self.use_normalized_baseline,
                "dynamic_trauma_active": self.enable_dynamic_trauma,
                "deadband_boundaries": {
                    "lower_lock_threshold": self.lower_lock,
                    "upper_escape_threshold": self.upper_escape
                }
            },
            "turn_trajectory": trajectory
        }


def main():
    parser = argparse.ArgumentParser(description="APEX Decay Simulation Runner v2.0")
    parser.add_argument("--lambda-decay", type=float, default=0.035, help="Base decay constant")
    parser.add_argument("--scenario", type=str, default="ACUTE_BETRAYAL_REPAIR", 
                        choices=["ACUTE_BETRAYAL_REPAIR", "CHRONIC_LOW_ENTROPY_DRIFT", "REPEATED_TRAUMA_COMPOUNDING"])
    parser.add_argument("--legacy-001", action="store_true", help="Use legacy 0.01 baseline instead of 1.00")
    parser.add_argument("--disable-trauma", action="store_true", help="Disable dynamic trauma accumulation")
    parser.add_argument("--output", type=str, default="apex_decay_telemetry_v2.json", help="Output file path")
    args = parser.parse_args()

    harness = ApexDecayHarnessV2(
        base_lambda=args.lambda_decay,
        use_normalized_baseline=not args.legacy_001,
        enable_dynamic_trauma=not args.disable_trauma
    )
    run_id = f"RUN_V2_{int(args.lambda_decay * 1000)}_{args.scenario}"
    telemetry = harness.execute_scenario(run_id, args.scenario)

    with open(args.output, "w") as f:
        json.dump(telemetry, f, indent=2)

    print(f"[STATUS: SUCCESS] Simulation executed: {args.output}")
    print(f"Total turns: {telemetry['simulation_metadata']['total_turns']} | Scenario: {args.scenario}")
    print(f"Final Trauma Load: {telemetry['turn_trajectory'][-1]['computed_metrics']['trauma_load']}")


if __name__ == "__main__":
    main()

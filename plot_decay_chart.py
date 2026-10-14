"""
plot_decay_chart.py
Renders the ACUTE_BETRAYAL_REPAIR trajectory from apex_decay_harness-v2.py.

Optional dependency: matplotlib (NOT required by the core engine, which is
stdlib only). Install with `pip install matplotlib` to use this script.

Usage: python3 plot_decay_chart.py [output.png]
"""
import os
import sys
from importlib import util

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
spec = util.spec_from_file_location("apex_decay_harness_v2", os.path.join(HERE, "apex_decay_harness-v2.py"))
harness_mod = util.module_from_spec(spec)
spec.loader.exec_module(harness_mod)


def run(enable_trauma):
    h = harness_mod.ApexDecayHarnessV2(base_lambda=0.035, enable_dynamic_trauma=enable_trauma)
    return h.execute_scenario("PLOT", "ACUTE_BETRAYAL_REPAIR")["turn_trajectory"]


def main(out):
    traj = run(True)
    traj_nt = run(False)
    t = [x["t"] for x in traj]
    S = [x["computed_metrics"]["S_smooth"] for x in traj]
    S_nt = [x["computed_metrics"]["S_smooth"] for x in traj_nt]
    E = [x["inputs"]["E"] for x in traj]
    V = [x["inputs"]["V"] for x in traj]
    T = [x["inputs"]["T"] for x in traj]
    nmap = {"GUT": 0, "HEAD": 1, "HEART": 2}
    node = [nmap[x["computed_metrics"]["active_node"]] for x in traj]

    bg, ax_bg, fg = "#0f141c", "#161b24", "#c9d1d9"
    plt.rcParams.update({"text.color": fg, "axes.labelcolor": fg, "xtick.color": "#8b949e",
                         "ytick.color": "#8b949e", "axes.edgecolor": "#30363d", "font.size": 10})
    fig = plt.figure(figsize=(14, 11), facecolor=bg)
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1.25], hspace=0.12, left=0.12, right=0.97, top=0.90, bottom=0.17)
    ax = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax)
    for a in (ax, ax2):
        a.set_facecolor(ax_bg)
        a.grid(color="#2a313c", ls="--", lw=0.6)
    bands = [(0.78, 1.05, "#2ea043", 0.15, "HEART Bulkhead (S > 0.78)"),
             (0.35, 0.78, "#1f6feb", 0.13, "HEAD Bulkhead (0.35 - 0.78)"),
             (0.32, 0.35, "#d29922", 0.45, "Hysteresis Deadband (0.32 - 0.35)"),
             (0.0, 0.32, "#da3633", 0.18, "GUT Bulkhead (S < 0.32)")]
    for lo, hi, c, al, _ in bands:
        ax.axhspan(lo, hi, color=c, alpha=al, lw=0)
    ax.axvspan(10.5, 20.5, color="#da3633", alpha=0.10, lw=0)
    ax.axvspan(20.5, 40.5, color="#d29922", alpha=0.08, lw=0)
    ax.plot(t, S, color="#58a6ff", lw=2.8, label=r"$S_{smooth}$ (dynamic trauma, default)")
    ax.plot(t, S_nt, color="#79c0ff", lw=1.8, ls=(0, (4, 2)), label=r"$S_{smooth}$ (--disable-trauma)")
    ax.plot(t, E, color="#f85149", ls="--", lw=1.8, label=r"Entropy ($E$)")
    ax.plot(t, V, color="#56d364", ls=":", lw=2, label=r"Validation ($V$)")
    ax.plot(t, T, color="#a5a0d8", ls="-.", lw=1.6, label=r"Trust ($T$)")
    ax.set_ylim(-0.02, 1.22)
    ax.set_xlim(-0.5, 40.5)
    ax.set_ylabel("Normalized Metric Value", fontweight="bold")
    box = dict(boxstyle="round,pad=0.45", fc="#1c2129", alpha=0.95)
    ax.text(15.5, 1.13, "PHASE 2: RELATIONAL SHOCK (t=11-20)\nE=0.90, V=0.00 forces S_MOD to 0\nImmediate GUT collapse",
            ha="center", va="center", fontsize=8.6, color="#ff7b72", fontweight="bold", bbox={**box, "ec": "#f85149"})
    ax.text(30.5, 1.13, f"PHASE 3: REPAIR HORIZON (t=21-40)\nS_smooth climbs but stays in GUT by t=40\n"
            f"final {S[-1]:.3f} (trauma) vs {S_nt[-1]:.3f} (no trauma)",
            ha="center", va="center", fontsize=8.6, color="#e3b341", fontweight="bold", bbox={**box, "ec": "#d29922"})
    h, l = ax.get_legend_handles_labels()
    h += [Patch(color=b[2], alpha=min(b[3] * 2, 0.7)) for b in bands]
    l += [b[4] for b in bands]
    ax.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, -0.32), bbox_transform=ax2.transAxes, ncol=3,
              frameon=True, facecolor="#1c2129", edgecolor="#30363d", fontsize=9, labelcolor=fg)
    ax2.step(t, node, where="mid", color="#8b949e", lw=1.4)
    cols = {2: "#56d364", 1: "#58a6ff", 0: "#f85149"}
    ax2.scatter(t, node, c=[cols[n] for n in node], s=60, edgecolors="white", linewidths=0.8, zorder=3)
    ax2.set_yticks([0, 1, 2])
    ax2.set_yticklabels(["GUT NODE", "HEAD NODE", "HEART NODE"], fontweight="bold")
    ax2.set_ylim(-0.4, 2.4)
    ax2.set_ylabel("Active Node (default)", fontweight="bold")
    ax2.set_xlabel("Conversational Turn Index", fontweight="bold")
    plt.setp(ax.get_xticklabels(), visible=False)
    fig.suptitle("APEX Deterministic Cognitive State Engine v2.1: Multi-Turn Attractor Dynamics & Allostatic Recovery",
                 fontsize=14, fontweight="bold", color="white", y=0.955)
    fig.text(0.5, 0.015, "Output of apex_decay_harness-v2.py (ACUTE_BETRAYAL_REPAIR), simulation — not measured on a live model.",
             ha="center", fontsize=10, style="italic", color="#8b949e")
    fig.savefig(out, dpi=130, facecolor=bg)
    print(f"Saved {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "apex_s_index_decay_simulation_v21.png")

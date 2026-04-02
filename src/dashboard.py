"""
dashboard.py
============
Production KPI Dashboard — ASCII + Chart data for terminal or export
Generates matplotlib charts for reports and LinkedIn portfolio visuals.

Author: Project Engineer | Mustard Oil Factory (3 yrs exp)
"""

import os
import datetime
import random
from pathlib import Path

Path("reports/charts").mkdir(parents=True, exist_ok=True)


def generate_sample_data(days=30):
    """Generate 30-day historical production KPI data."""
    data = []
    base_date = datetime.date.today() - datetime.timedelta(days=days)
    for i in range(days):
        date = base_date + datetime.timedelta(days=i)
        # Simulate realistic trends: yield improves mid-month after maintenance
        trend = 0.05 * i if i < 15 else 0.05 * (30 - i)
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "day": i + 1,
            "yield_pct": round(31.5 + trend + random.gauss(0, 0.6), 2),
            "throughput": round(115 + trend * 2 + random.gauss(0, 4), 1),
            "ffa_pct": round(1.2 - trend * 0.02 + random.gauss(0, 0.15), 3),
            "energy_kwh_t": round(52 - trend * 0.3 + random.gauss(0, 2), 1),
            "cake_oil_pct": round(7.2 - trend * 0.05 + random.gauss(0, 0.3), 2),
            "downtime_hr": round(max(0, random.gauss(1.2, 0.8)), 1),
            "batches": random.randint(2, 4),
        })
    return data


def create_charts(data):
    """Generate matplotlib KPI charts — saved to reports/charts/."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.gridspec import GridSpec
        import datetime as dt

        dates = [dt.datetime.strptime(d["date"], "%Y-%m-%d") for d in data]
        yields = [d["yield_pct"] for d in data]
        throughputs = [d["throughput"] for d in data]
        ffas = [d["ffa_pct"] for d in data]
        energies = [d["energy_kwh_t"] for d in data]
        downtimes = [d["downtime_hr"] for d in data]

        # ── Chart 1: 30-Day KPI Overview ──────────────────────────
        fig = plt.figure(figsize=(16, 10))
        fig.patch.set_facecolor('#1a1a2e')
        gs = GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

        plot_cfg = [
            (gs[0, 0], yields, "Oil Yield (%)", "#f4c430", 33.0, "Target 33%"),
            (gs[0, 1], throughputs, "Throughput (kg/hr)", "#4fc3f7", 120, "Target 120"),
            (gs[0, 2], ffas, "FFA (%)", "#ef5350", 2.0, "FSSAI Limit"),
            (gs[1, 0], energies, "Specific Energy (kWh/t)", "#aed581", 45.0, "Benchmark"),
            (gs[1, 1], downtimes, "Downtime (hr/day)", "#ff8a65", 2.0, "Alarm >2hr"),
        ]

        for pos, values, title, color, threshold, thresh_label in plot_cfg:
            ax = fig.add_subplot(pos)
            ax.set_facecolor('#16213e')
            ax.plot(dates, values, color=color, linewidth=2, alpha=0.9)
            ax.fill_between(dates, values, alpha=0.15, color=color)
            ax.axhline(threshold, color='white', linewidth=0.8,
                       linestyle='--', alpha=0.5, label=thresh_label)
            ax.set_title(title, color='white', fontsize=10, fontweight='bold', pad=8)
            ax.tick_params(colors='#aaaaaa', labelsize=7)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=30)
            for spine in ax.spines.values():
                spine.set_edgecolor('#333355')
            ax.legend(fontsize=7, labelcolor='white',
                      facecolor='#1a1a2e', edgecolor='none')

        # Pie chart: grade distribution
        ax_pie = fig.add_subplot(gs[1, 2])
        ax_pie.set_facecolor('#16213e')
        grades = ['Agmark Gr-1', 'Agmark Gr-2', 'FSSAI Edible', 'Sub-Std']
        sizes = [35, 45, 15, 5]
        colors_pie = ['#4caf50', '#8bc34a', '#ffc107', '#ef5350']
        wedges, texts, autotexts = ax_pie.pie(
            sizes, labels=grades, colors=colors_pie,
            autopct='%1.0f%%', startangle=90,
            textprops={'color': 'white', 'fontsize': 8})
        for at in autotexts:
            at.set_fontsize(7)
        ax_pie.set_title("Oil Grade Distribution", color='white',
                          fontsize=10, fontweight='bold', pad=8)

        fig.suptitle(
            "🌾  Mustard Oil Factory — 30-Day Production KPI Dashboard",
            color='#f4c430', fontsize=14, fontweight='bold', y=0.98)

        plt.savefig("reports/charts/kpi_dashboard.png", dpi=150,
                    bbox_inches='tight', facecolor='#1a1a2e')
        plt.close()
        print("    ✅ KPI Dashboard → reports/charts/kpi_dashboard.png")

        # ── Chart 2: Yield vs Throughput Scatter ──────────────────
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        fig2.patch.set_facecolor('#1a1a2e')
        ax2.set_facecolor('#16213e')
        scatter = ax2.scatter(throughputs, yields,
                              c=ffas, cmap='RdYlGn_r',
                              s=80, alpha=0.8, edgecolors='white', linewidths=0.3)
        cbar = plt.colorbar(scatter, ax=ax2)
        cbar.set_label('FFA %', color='white')
        cbar.ax.yaxis.set_tick_params(color='white')
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white')
        ax2.axhline(33.0, color='#f4c430', linestyle='--',
                    linewidth=1, alpha=0.7, label='Yield Target 33%')
        ax2.axvline(120, color='#4fc3f7', linestyle='--',
                    linewidth=1, alpha=0.7, label='Throughput Target 120 kg/hr')
        ax2.set_xlabel("Throughput (kg/hr)", color='white')
        ax2.set_ylabel("Oil Yield (%)", color='white')
        ax2.set_title("Yield vs Throughput (colour = FFA)",
                      color='white', fontweight='bold')
        ax2.tick_params(colors='#aaaaaa')
        for spine in ax2.spines.values():
            spine.set_edgecolor('#333355')
        ax2.legend(facecolor='#1a1a2e', labelcolor='white',
                   edgecolor='none', fontsize=8)
        plt.tight_layout()
        plt.savefig("reports/charts/yield_scatter.png", dpi=150,
                    bbox_inches='tight', facecolor='#1a1a2e')
        plt.close()
        print("    ✅ Yield Scatter → reports/charts/yield_scatter.png")
        return True

    except ImportError:
        print("    ⚠️  matplotlib not available — skipping chart generation")
        return False


def print_kpi_table(data):
    """Print ASCII KPI summary table."""
    recent = data[-7:]  # last 7 days
    avg_yield = sum(d['yield_pct'] for d in recent) / len(recent)
    avg_ffa = sum(d['ffa_pct'] for d in recent) / len(recent)
    avg_energy = sum(d['energy_kwh_t'] for d in recent) / len(recent)
    avg_tp = sum(d['throughput'] for d in recent) / len(recent)
    total_batches = sum(d['batches'] for d in data)

    print("\n  ╔══════════════════════════════════════════════════╗")
    print("  ║      30-DAY PRODUCTION KPI SUMMARY               ║")
    print("  ╠══════════════════════════════════════════════════╣")
    print(f"  ║  Total Batches Processed    : {total_batches:<19d}║")
    print(f"  ║  Avg Oil Yield (7-day)      : {avg_yield:<18.2f}%║")
    print(f"  ║  Avg Throughput (7-day)     : {avg_tp:<15.1f}kg/hr║")
    print(f"  ║  Avg FFA (7-day)            : {avg_ffa:<19.3f}║")
    print(f"  ║  Avg Specific Energy (7-day): {avg_energy:<12.1f}kWh/t║")
    print("  ╚══════════════════════════════════════════════════╝\n")

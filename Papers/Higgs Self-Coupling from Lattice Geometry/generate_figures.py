#!/usr/bin/env python3
"""
Generate figures for Paper 075 contest submission.
Three figures for the geometry paper:
  1. 3D unit cube coordination shells (z₁, z₂)
  2. Mexican hat potential V(χ)
  3. Derivation chain flowchart
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
from pathlib import Path

OUT = Path(__file__).resolve().parent
DPI = 300

# ============================================================================
# Figure 1: 3D Coordination Shells
# ============================================================================
def fig_coordination_shells():
    """
    Show the origin point and its coordination shells on a 3D cubic lattice.
    - Origin = black
    - z₁ = 6 face-center neighbors (blue)      at distance 1
    - z₁' = 12 edge-center neighbors (orange)   at distance √2
    - z₁'' = 8 corner neighbors (red/green)     at distance √3
    Total z₂ = 2D² = 2(4²) = 32 second-shell sites
    
    But wait - for the PAPER, z₁=8 (first coord shell = corners of unit cube)
    and z₂=32 (second coord shell = all of NN+NNN on hypercubic D_st=4).
    
    For the 3D visualization we show the modes on the unit cell:
    - DC mode (1): center
    - Face modes (6): ±k along axes 
    - Edge modes (12): ±k along face diagonals
    - Corner modes (8): ±k along body diagonals
    """
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection='3d')
    
    # Draw the unit cube wireframe
    for s in [0, 1]:
        for t in [0, 1]:
            # x-direction edges
            ax.plot([0, 1], [s, s], [t, t], 'k-', alpha=0.15, linewidth=0.8)
            # y-direction edges
            ax.plot([s, s], [0, 1], [t, t], 'k-', alpha=0.15, linewidth=0.8)
            # z-direction edges  
            ax.plot([s, s], [t, t], [0, 1], 'k-', alpha=0.15, linewidth=0.8)
    
    # Second cube wireframe (periodic image hint)
    offset = 1.0
    for s in [0, 1]:
        for t in [0, 1]:
            ax.plot([offset, offset+1], [s, s], [t, t], 'k-', alpha=0.06, linewidth=0.5)
            ax.plot([s, s], [offset, offset+1], [t, t], 'k-', alpha=0.06, linewidth=0.5)
            ax.plot([s, s], [t, t], [offset, offset+1], 'k-', alpha=0.06, linewidth=0.5)

    # Center of unit cell = DC mode (origin)
    center = np.array([0.5, 0.5, 0.5])
    
    # Face modes: 6 points (face centers)
    face_pts = np.array([
        [0, 0.5, 0.5], [1, 0.5, 0.5],  # ±x
        [0.5, 0, 0.5], [0.5, 1, 0.5],  # ±y
        [0.5, 0.5, 0], [0.5, 0.5, 1],  # ±z
    ])
    
    # Edge modes: 12 points (edge midpoints)
    edge_pts = np.array([
        [0, 0, 0.5], [1, 0, 0.5], [0, 1, 0.5], [1, 1, 0.5],  # z-edges
        [0, 0.5, 0], [1, 0.5, 0], [0, 0.5, 1], [1, 0.5, 1],  # y-edges
        [0.5, 0, 0], [0.5, 1, 0], [0.5, 0, 1], [0.5, 1, 1],  # x-edges
    ])
    
    # Corner modes: 8 points (vertices)
    corner_pts = np.array([
        [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
        [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1],
    ])
    
    # Plot points
    # DC mode (center)
    ax.scatter(*center, color='black', s=200, zorder=5, edgecolors='white', linewidths=1.5,
               label=f'DC mode (1)')
    
    # Face modes
    ax.scatter(face_pts[:, 0], face_pts[:, 1], face_pts[:, 2],
               color='#2196F3', s=120, zorder=4, edgecolors='white', linewidths=1,
               label=f'Face modes (6)', marker='o')
    
    # Edge modes  
    ax.scatter(edge_pts[:, 0], edge_pts[:, 1], edge_pts[:, 2],
               color='#FF9800', s=100, zorder=4, edgecolors='white', linewidths=1,
               label=f'Edge modes (12)', marker='s')
    
    # Corner modes
    ax.scatter(corner_pts[:, 0], corner_pts[:, 1], corner_pts[:, 2],
               color='#F44336', s=100, zorder=4, edgecolors='white', linewidths=1,
               label=f'Corner modes (8)', marker='^')
    
    # Draw lines from center to face modes (dotted)
    for pt in face_pts:
        ax.plot([center[0], pt[0]], [center[1], pt[1]], [center[2], pt[2]],
                color='#2196F3', alpha=0.3, linewidth=1, linestyle='--')
    
    # Annotations
    ax.text(0.5, 0.5, 0.5 + 0.12, 'DC', ha='center', fontsize=9, fontweight='bold',
            color='black')
    
    # Cumulative labels on the right
    ax.text(1.25, 0.5, 1.1, r'$\chi_0 = 1 + 6 + 12 = 19$', fontsize=11,
            fontweight='bold', color='#333333')
    ax.text(1.25, 0.5, 0.9, r'Corners $= 2^D = 8$', fontsize=9,
            color='#F44336')
    ax.text(1.25, 0.5, 0.7, r'Total $= 3^D = 27$', fontsize=9,
            color='#666666')
    
    ax.set_xlabel('x', fontsize=10)
    ax.set_ylabel('y', fontsize=10)
    ax.set_zlabel('z', fontsize=10)
    ax.set_title('Discrete Laplacian Mode Degeneracies on 3D Unit Cell\n'
                 r'$\chi_0(D) = 3^D - 2^D$: non-corner modes', fontsize=12, pad=15)
    
    ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
    ax.view_init(elev=25, azim=135)
    ax.set_xlim(-0.15, 1.45)
    ax.set_ylim(-0.15, 1.15)
    ax.set_zlim(-0.15, 1.15)
    
    # Clean up tick labels
    ax.set_xticks([0, 0.5, 1])
    ax.set_yticks([0, 0.5, 1])
    ax.set_zticks([0, 0.5, 1])
    
    plt.tight_layout()
    path = OUT / 'fig_coordination_shells.pdf'
    fig.savefig(path, dpi=DPI, bbox_inches='tight')
    fig.savefig(OUT / 'fig_coordination_shells.png', dpi=DPI, bbox_inches='tight')
    print(f'Saved: {path}')
    plt.close(fig)


# ============================================================================
# Figure 2: Mexican Hat Potential
# ============================================================================
def fig_mexican_hat():
    """
    Plot V(χ) = λ(χ² - χ₀²)² showing the double-well potential.
    Show both minima at ±χ₀, the unstable maximum at χ=0,
    and the physical interpretation.
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    chi0 = 19.0
    lam = 4.0 / 31.0
    
    chi = np.linspace(-28, 28, 1000)
    V = lam * (chi**2 - chi0**2)**2
    V_norm = V / (lam * chi0**4)  # Normalize to max = 1
    
    ax.plot(chi, V_norm, 'k-', linewidth=2)
    ax.fill_between(chi, V_norm, alpha=0.05, color='blue')
    
    # Mark minima
    ax.plot(-chi0, 0, 'o', color='#F44336', markersize=12, zorder=5, 
            markeredgecolor='white', markeredgewidth=1.5)
    ax.plot(chi0, 0, 'o', color='#2196F3', markersize=12, zorder=5,
            markeredgecolor='white', markeredgewidth=1.5)
    
    # Mark maximum
    ax.plot(0, 1.0, 'o', color='#FF9800', markersize=10, zorder=5,
            markeredgecolor='white', markeredgewidth=1.5)
    
    # Annotations
    ax.annotate(r'$+\chi_0 = +19$' + '\n(our vacuum)', 
                xy=(chi0, 0), xytext=(chi0 + 3, 0.35),
                fontsize=10, ha='left',
                arrowprops=dict(arrowstyle='->', color='#2196F3', lw=1.5),
                color='#2196F3', fontweight='bold')
    
    ax.annotate(r'$-\chi_0 = -19$' + '\n(BH interior)', 
                xy=(-chi0, 0), xytext=(-chi0 - 3, 0.35),
                fontsize=10, ha='right',
                arrowprops=dict(arrowstyle='->', color='#F44336', lw=1.5),
                color='#F44336', fontweight='bold')
    
    ax.annotate(r'$V(0) = \lambda\chi_0^4$' + '\n(unstable)', 
                xy=(0, 1.0), xytext=(7, 0.85),
                fontsize=9, ha='left',
                arrowprops=dict(arrowstyle='->', color='#FF9800', lw=1.5),
                color='#FF9800')
    
    # Higgs oscillation frequency annotation
    ax.annotate(r'$\omega_H = \sqrt{8\lambda}\,\chi_0 \approx 19.3$',
                xy=(chi0 + 2, 0.04), xytext=(chi0 + 2, 0.15),
                fontsize=9, ha='center', color='#666666',
                arrowprops=dict(arrowstyle='<->', color='#666666', lw=1))
    
    ax.set_xlabel(r'$\chi$', fontsize=13)
    ax.set_ylabel(r'$V(\chi)\, /\, \lambda\chi_0^4$', fontsize=13)
    ax.set_title(r'Mexican Hat Potential: $V(\chi) = \lambda\,(\chi^2 - \chi_0^2)^2$'
                 r',  $\lambda = 4/31$', fontsize=12)
    
    ax.set_ylim(-0.05, 1.15)
    ax.set_xlim(-28, 35)
    ax.axhline(0, color='gray', linewidth=0.5, linestyle='-')
    ax.axvline(0, color='gray', linewidth=0.5, linestyle='--', alpha=0.3)
    
    # Z2 symmetry annotation
    ax.annotate('', xy=(-chi0, -0.04), xytext=(chi0, -0.04),
                arrowprops=dict(arrowstyle='<->', color='purple', lw=1.5))
    ax.text(0, -0.04, r'$\mathbb{Z}_2$ symmetry: $V(\chi) = V(-\chi)$',
            ha='center', va='top', fontsize=9, color='purple', fontstyle='italic')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    path = OUT / 'fig_mexican_hat.pdf'
    fig.savefig(path, dpi=DPI, bbox_inches='tight')
    fig.savefig(OUT / 'fig_mexican_hat.png', dpi=DPI, bbox_inches='tight')
    print(f'Saved: {path}')
    plt.close(fig)


# ============================================================================
# Figure 3: Derivation Chain Flowchart  
# ============================================================================
def fig_derivation_chain():
    """
    Flowchart: Axiom 1 + Axiom 2 → D=3 → χ₀=19 → coordination shells → λ=4/31
    """
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.5)
    ax.axis('off')
    
    # Color scheme
    axiom_color = '#E8EAF6'    # light indigo
    derive_color = '#E3F2FD'   # light blue  
    predict_color = '#FFF3E0'  # light orange
    result_color = '#E8F5E9'   # light green
    border_axiom = '#3F51B5'
    border_derive = '#1976D2'
    border_predict = '#E65100'
    border_result = '#2E7D32'
    
    def draw_box(x, y, w, h, text, facecolor, edgecolor, fontsize=10, bold=False):
        box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.15",
                             facecolor=facecolor, edgecolor=edgecolor,
                             linewidth=1.8)
        ax.add_patch(box)
        weight = 'bold' if bold else 'normal'
        ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
                fontweight=weight, color='#333333',
                linespacing=1.4)
    
    def draw_arrow(x1, y1, x2, y2, color='#666666'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.8,
                                    connectionstyle='arc3,rad=0'))
    
    # Row 1: Axioms (top)
    draw_box(2.5, 5.8, 3.8, 0.7,
             'Axiom 1: Discrete lattice\nnearest-neighbor interactions',
             axiom_color, border_axiom, fontsize=9, bold=True)
    
    draw_box(7.5, 5.8, 3.8, 0.7,
             'Axiom 2: Rotating bound states\n(angular momentum quantization)',
             axiom_color, border_axiom, fontsize=9, bold=True)
    
    # Row 2: D=3 and chi_0=19
    draw_box(2.5, 4.4, 3.2, 0.7,
             r'$D = 3$ (spatial dimensions)' + '\nstable orbits + cross product',
             derive_color, border_derive, fontsize=9)
    
    draw_box(7.5, 4.4, 3.2, 0.7,
             r'$\chi_0 = 3^3 - 2^3 = 19$' + '\nLaplacian mode counting',
             derive_color, border_derive, fontsize=9, bold=True)
    
    # Row 3: Coordination shells
    draw_box(5.0, 3.0, 5.0, 0.8,
             r'$D_{st} = D + 1 = 4$ spacetime dimensions' + '\n'
             r'Second shell: $z_2 = 2D_{st}^2 = 32$ sites,'
             r'  physical channels: $z_2 - 1 = 31$',
             predict_color, border_predict, fontsize=9)
    
    # Row 4: The prediction
    draw_box(5.0, 1.6, 5.5, 0.9,
             r'$\lambda = D_{st}\, /\, (2\,D_{st}^2 - 1)'
             r' = 4/31 \approx 0.12903$'
             + '\n' + r'Vertex coupling = dimensions $\div$ neighbor channels',
             result_color, border_result, fontsize=11, bold=True)
    
    # Row 5: Comparison
    draw_box(5.0, 0.4, 5.0, 0.55,
             r'SM measured: $\lambda_{SM} = 0.1291 \pm 0.05$  '
             r'$\rightarrow$  error: 0.27%',
             '#FAFAFA', '#999999', fontsize=9)
    
    # Arrows
    draw_arrow(2.5, 5.45, 2.5, 4.75, border_axiom)
    draw_arrow(7.5, 5.45, 7.5, 4.75, border_axiom)
    draw_arrow(2.5, 4.05, 4.0, 3.42, border_derive)
    draw_arrow(7.5, 4.05, 6.0, 3.42, border_derive)
    draw_arrow(5.0, 2.58, 5.0, 2.07, border_predict)
    draw_arrow(5.0, 1.15, 5.0, 0.70, border_result)
    
    ax.set_title('Derivation Chain: From Lattice Axioms to Higgs Self-Coupling',
                 fontsize=12, fontweight='bold', pad=10)
    
    plt.tight_layout()
    path = OUT / 'fig_derivation_chain.pdf'
    fig.savefig(path, dpi=DPI, bbox_inches='tight')
    fig.savefig(OUT / 'fig_derivation_chain.png', dpi=DPI, bbox_inches='tight')
    print(f'Saved: {path}')
    plt.close(fig)


# ============================================================================
# Main
# ============================================================================
if __name__ == '__main__':
    print(f'Output directory: {OUT}')
    print()
    fig_coordination_shells()
    fig_mexican_hat()
    fig_derivation_chain()
    print('\nAll figures generated.')

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import os
import io
import tempfile
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="Lunar Ice Mission Planner",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0d0d2b 0%, #1a237e 50%, #0d47a1 100%);
        padding: 30px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
        border: 1px solid #3949ab;
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2.2em;
        font-weight: 800;
        letter-spacing: 3px;
        margin: 0;
        text-shadow: 0 0 20px rgba(100,181,246,0.5);
    }
    .main-header p {
        color: #90caf9;
        font-size: 1em;
        margin: 8px 0 0 0;
        letter-spacing: 2px;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a237e, #0d47a1);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        border: 1px solid #3949ab;
        color: white;
        margin: 4px;
    }
    .metric-value {
        font-size: 1.8em;
        font-weight: bold;
        color: #64b5f6;
    }
    .metric-label {
        font-size: 0.8em;
        color: #b0bec5;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .status-bar {
        background: #1b5e20;
        color: #a5d6a7;
        padding: 10px 20px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        letter-spacing: 1px;
        margin: 10px 0;
    }
    .section-header {
        color: #64b5f6;
        font-size: 1.1em;
        font-weight: bold;
        letter-spacing: 2px;
        text-transform: uppercase;
        border-bottom: 2px solid #1a237e;
        padding-bottom: 5px;
        margin: 15px 0 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Import modules
from modules.radar_processor import (
    load_radar_data, generate_demo_radar,
    calculate_cpr, calculate_dop,
    detect_ice_regions, estimate_ice_volume
)
from modules.terrain_analyzer import (
    analyze_terrain, generate_demo_terrain, select_landing_site
)
from modules.rover_path import astar_path, calculate_path_metrics
from modules.report_generator import generate_pdf_report

# ── Chunk size for large file writing (handle ~720MB–1GB datasets) ──
CHUNK_SIZE = 64 * 1024 * 1024  # 64 MB per chunk

def save_uploaded_file_chunked(uploaded_file, suffix='.tif'):
    """
    Write an uploaded file to disk in 64 MB chunks.
    Handles datasets up to ~1 GB without loading everything into RAM at once.
    Returns the path to the temporary file.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        uploaded_file.seek(0)
        while True:
            chunk = uploaded_file.read(CHUNK_SIZE)
            if not chunk:
                break
            tmp.write(chunk)
    finally:
        tmp.close()
    return tmp.name

# ── Header ──────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🚀 LUNAR ICE MISSION PLANNER</h1>
    <p>CHANDRAYAAN-2 ● DFSAR + OHRC ● BHARATIYA ANTARIKSH HACKATHON</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛰 MISSION CONTROL")
    st.markdown("---")

    mode = st.radio(
        "Select Mode",
        ["🔬 Demo Mission", "📂 Upload Dataset"],
        help="Demo mode uses built-in synthetic data. Upload mode uses your Chandrayaan-2 files."
    )

    st.markdown("---")
    st.markdown("### ⚙️ DETECTION PARAMETERS")

    cpr_threshold = st.slider(
        "CPR Threshold",
        min_value=0.5, max_value=2.5, value=1.0, step=0.1,
        help="Circular Polarization Ratio. Values above this indicate possible ice."
    )

    dop_threshold = st.slider(
        "DOP Threshold",
        min_value=0.1, max_value=0.8, value=0.3, step=0.05,
        help="Degree of Polarization. Values below this suggest ice in shadowed regions."
    )

    pixel_size = st.slider(
        "Pixel Size (meters)",
        min_value=5, max_value=75, value=30, step=5,
        help="Ground resolution of radar data. DFSAR = ~30m."
    )

    st.markdown("---")
    st.markdown("### 📡 INSTRUMENT INFO")
    st.info("**DFSAR**: Dual Frequency SAR\nL-Band & S-Band radar\nDetects subsurface ice")
    st.info("**OHRC**: Orbital High Resolution Camera\n25 cm/pixel\nTerrain mapping")

    st.markdown("---")
    st.markdown("### 🌙 MISSION INFO")
    st.markdown("""
    **Target**: Lunar South Pole  
    **Objective**: Ice Detection  
    **Satellite**: Chandrayaan-2  
    **Algorithm**: CPR + DOP + A*
    """)

# ── Main Content ──────────────────────────────────────────────
if "🔬 Demo" in mode:
    st.markdown('<div class="status-bar">🟢 DEMO MODE ACTIVE — Pre-loaded Synthetic Chandrayaan-2 Data</div>',
                unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.info("This demo uses scientifically realistic synthetic data modeled after actual "
                "Chandrayaan-2 DFSAR observations of the lunar south pole. All algorithms are identical "
                "to those used with real data.")
    with col2:
        if st.button("🚀 RUN DEMO ANALYSIS", type="primary", use_container_width=True):
            st.session_state['run_analysis'] = True
            st.session_state['demo_mode'] = True

    run_analysis = st.session_state.get('run_analysis', False)
    demo_mode = st.session_state.get('demo_mode', False)

else:
    st.markdown('<div class="section-header">Upload Chandrayaan-2 Datasets</div>',
                unsafe_allow_html=True)

    # ── Large-file notice ────────────────────────────────────
    st.info(
        "📦 **Large dataset support enabled** — files up to **1 GB** accepted. "
        "Typical DFSAR/OHRC datasets (~720 MB) upload fine. "
        "If you see a size error, ensure `.streamlit/config.toml` contains `maxUploadSize = 1024`."
    )

    col1, col2 = st.columns(2)
    with col1:
        dfsar_file = st.file_uploader(
            "📡 Upload DFSAR Radar Data",
            type=['zip', 'tif', 'tiff', 'img'],
            help="Upload the DFSAR ZIP or GeoTIFF file from ISDA (up to ~1 GB supported)"
        )
        if dfsar_file:
            file_size_mb = dfsar_file.size / (1024 * 1024)
            st.success(f"✅ Radar loaded: {dfsar_file.name}  ({file_size_mb:.1f} MB)")

    with col2:
        ohrc_file = st.file_uploader(
            "📷 Upload OHRC Imagery",
            type=['zip', 'tif', 'tiff', 'jpg', 'png', 'img'],
            help="Upload the OHRC ZIP or image file from ISDA (up to ~1 GB supported)"
        )
        if ohrc_file:
            file_size_mb = ohrc_file.size / (1024 * 1024)
            st.success(f"✅ Image loaded: {ohrc_file.name}  ({file_size_mb:.1f} MB)")

    run_button = st.button(
        "🔍 RUN MISSION ANALYSIS",
        type="primary",
        use_container_width=True,
        disabled=(dfsar_file is None and ohrc_file is None)
    )

    run_analysis = run_button
    demo_mode = False

    if not dfsar_file and not ohrc_file:
        st.warning("Upload at least one dataset, or switch to Demo Mode to see the prototype in action.")

# ── Analysis ──────────────────────────────────────────────────
if run_analysis or st.session_state.get('analysis_done', False):

    if run_analysis:
        progress = st.progress(0)
        status = st.empty()

        status.markdown("**🔄 Loading radar data...**")
        progress.progress(10)

        if demo_mode or st.session_state.get('demo_mode', False):
            radar_data = generate_demo_radar()
            terrain_data = generate_demo_terrain()
        else:
            # ── DFSAR — chunked write for large files (~720 MB–1 GB) ──
            try:
                tmp_path = save_uploaded_file_chunked(dfsar_file, suffix='.tif')
                status.markdown("**🔄 Parsing radar file (large dataset — please wait)...**")
                radar_data, _, _, _ = load_radar_data(tmp_path)
                os.unlink(tmp_path)
            except Exception as e:
                st.warning(f"Could not parse DFSAR file ({e}). Falling back to demo radar data.")
                radar_data = generate_demo_radar()

            # ── OHRC — chunked write, then open with PIL ──
            try:
                tmp_path_ohrc = save_uploaded_file_chunked(ohrc_file, suffix='.tif')
                status.markdown("**🔄 Parsing image file (large dataset — please wait)...**")
                img = Image.open(tmp_path_ohrc).convert('L')
                img = img.resize((512, 512))
                terrain_data = np.array(img, dtype=np.float32)[np.newaxis, :] / 255.0
                os.unlink(tmp_path_ohrc)
            except Exception as e:
                st.warning(f"Could not parse OHRC file ({e}). Falling back to demo terrain data.")
                terrain_data = generate_demo_terrain()

        status.markdown("**🔄 Calculating CPR and DOP...**")
        progress.progress(30)

        cpr_map = calculate_cpr(radar_data)
        dop_map = calculate_dop(radar_data)

        status.markdown("**🔄 Detecting ice regions...**")
        progress.progress(50)

        ice_mask, ice_probability = detect_ice_regions(cpr_map, dop_map, cpr_threshold, dop_threshold)
        ice_volume = estimate_ice_volume(ice_mask, pixel_size)

        status.markdown("**🔄 Analyzing terrain...**")
        progress.progress(65)

        slope, roughness, hazard = analyze_terrain(terrain_data)

        status.markdown("**🔄 Selecting landing site...**")
        progress.progress(75)

        landing = select_landing_site(ice_mask, slope, hazard, ice_probability)

        status.markdown("**🔄 Planning rover path...**")
        progress.progress(85)

        ice_positions = np.argwhere(ice_mask > 0)
        if len(ice_positions) > 0:
            land_pos = np.array([landing['row'], landing['col']])
            distances = np.linalg.norm(ice_positions - land_pos, axis=1)
            nearest_ice = tuple(ice_positions[np.argmin(distances)])
        else:
            nearest_ice = (256, 256)

        start = (landing['row'], landing['col'])
        path = astar_path(start, nearest_ice, hazard, slope)
        path_metrics = calculate_path_metrics(path, slope, pixel_size)

        status.markdown("**✅ Analysis complete!**")
        progress.progress(100)

        ice_score    = min(ice_volume['ice_area_km2'] / 0.5, 1.0) * 35
        land_score   = landing['score'] * 30
        path_score   = (1 - min(path_metrics['avg_slope'] / 15, 1)) * 20
        resource_score = min(ice_volume['water_mass_tonnes'] / 10000, 1.0) * 15
        mission_score = ice_score + land_score + path_score + resource_score

        st.session_state['results'] = {
            'cpr_map': cpr_map, 'dop_map': dop_map,
            'ice_mask': ice_mask, 'ice_probability': ice_probability,
            'slope': slope, 'hazard': hazard,
            'landing': landing, 'path': path, 'path_metrics': path_metrics,
            'ice_volume': ice_volume, 'mission_score': mission_score,
            'terrain_data': terrain_data
        }
        st.session_state['analysis_done'] = True

        import time; time.sleep(0.5)
        status.empty()
        progress.empty()
        st.rerun()

    # ── Display Results ──────────────────────────────────────
    if st.session_state.get('analysis_done'):
        r = st.session_state['results']

        st.markdown('<div class="status-bar">✅ MISSION ANALYSIS COMPLETE — All Systems Nominal</div>',
                    unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-header">📊 Mission Statistics</div>', unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns(5)
        iv = r['ice_volume']
        pm = r['path_metrics']
        ls = r['landing']

        with c1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{r['mission_score']:.0f}%</div>
                <div class="metric-label">Mission Score</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{iv['ice_area_km2']:.3f}</div>
                <div class="metric-label">Ice Area (km²)</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{iv['water_mass_tonnes']:,.0f}</div>
                <div class="metric-label">Water (tonnes)</div></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{pm['distance_m']:.0f}m</div>
                <div class="metric-label">Rover Distance</div></div>""", unsafe_allow_html=True)
        with c5:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{ls['slope_at_site']:.1f}°</div>
                <div class="metric-label">Landing Slope</div></div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-header">🗺️ Mission Maps</div>', unsafe_allow_html=True)

        fig, axes = plt.subplots(2, 3, figsize=(18, 11))
        fig.patch.set_facecolor('#0d0d2b')

        def style_ax(ax, title):
            ax.set_title(title, color='#64b5f6', fontsize=11, fontweight='bold', pad=8)
            ax.set_facecolor('#0d0d2b')
            ax.tick_params(colors='#90caf9', labelsize=7)
            for spine in ax.spines.values():
                spine.set_color('#1a237e')

        im0 = axes[0,0].imshow(r['cpr_map'], cmap='plasma', vmin=0, vmax=3)
        plt.colorbar(im0, ax=axes[0,0], label='CPR')
        style_ax(axes[0,0], '① CIRCULAR POLARIZATION RATIO (CPR)')
        axes[0,0].contour(r['cpr_map'] > cpr_threshold, colors='cyan', alpha=0.6, linewidths=0.8)

        im1 = axes[0,1].imshow(r['dop_map'], cmap='viridis', vmin=-1, vmax=1)
        plt.colorbar(im1, ax=axes[0,1], label='DOP')
        style_ax(axes[0,1], '② DEGREE OF POLARIZATION (DOP)')

        ice_cmap = LinearSegmentedColormap.from_list('ice', ['#0d0d2b','#1a237e','#00bcd4','#e3f2fd'])
        im2 = axes[0,2].imshow(r['ice_probability'], cmap=ice_cmap, vmin=0, vmax=1)
        plt.colorbar(im2, ax=axes[0,2], label='Probability')
        style_ax(axes[0,2], '③ ICE PROBABILITY MAP')
        axes[0,2].contour(r['ice_mask'], colors='#00e5ff', alpha=0.8, linewidths=1)

        im3 = axes[1,0].imshow(r['slope'], cmap='YlOrRd', vmin=0, vmax=20)
        plt.colorbar(im3, ax=axes[1,0], label='Degrees')
        style_ax(axes[1,0], '④ TERRAIN SLOPE MAP')

        im4 = axes[1,1].imshow(r['hazard'], cmap='hot', vmin=0, vmax=1)
        plt.colorbar(im4, ax=axes[1,1], label='Hazard Index')
        style_ax(axes[1,1], '⑤ HAZARD MAP')

        axes[1,2].imshow(r['ice_probability'], cmap=ice_cmap, vmin=0, vmax=1, alpha=0.7)
        axes[1,2].imshow(r['slope'], cmap='YlOrRd', vmin=0, vmax=20, alpha=0.3)

        ice_overlay = np.zeros((*r['ice_mask'].shape, 4))
        ice_overlay[r['ice_mask'] > 0] = [0, 0.9, 1, 0.5]
        axes[1,2].imshow(ice_overlay)

        ls_r, ls_c = r['landing']['row'], r['landing']['col']
        axes[1,2].plot(ls_c, ls_r, 'g^', markersize=14, markeredgecolor='white',
                       markeredgewidth=1.5, label='🟢 Landing Site', zorder=5)
        axes[1,2].add_patch(plt.Circle((ls_c, ls_r), 15, color='green', fill=False,
                                        linewidth=1.5, alpha=0.7))

        if r['path'] and len(r['path']) > 1:
            path_r = [p[0] for p in r['path']]
            path_c = [p[1] for p in r['path']]
            axes[1,2].plot(path_c, path_r, 'y-', linewidth=2, alpha=0.9,
                           label='🟡 Rover Path', zorder=4)
            axes[1,2].plot(path_c[-1], path_r[-1], 'b*', markersize=14,
                           markeredgecolor='white', markeredgewidth=1,
                           label='🔵 Ice Target', zorder=5)

        axes[1,2].legend(loc='upper right', fontsize=7, framealpha=0.85,
                         facecolor='#0d0d2b', edgecolor='#3949ab', labelcolor='white')
        style_ax(axes[1,2], '⑥ MISSION PLANNING MAP')

        plt.tight_layout(pad=2)
        st.pyplot(fig)
        plt.close()

        st.markdown("---")
        st.markdown('<div class="section-header">📋 Detailed Analysis</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🧊 Ice Detection**")
            st.metric("Ice Pixels",        f"{iv['ice_pixels']:,}")
            st.metric("Ice Area",          f"{iv['ice_area_km2']:.4f} km²")
            st.metric("Ice Volume",        f"{iv['ice_volume_m3']:,.0f} m³")
            st.metric("Water Equivalent",  f"{iv['water_mass_tonnes']:,.0f} tonnes")

        with col2:
            st.markdown("**🏔️ Landing Site**")
            st.metric("Safety Score",  f"{ls['score']*100:.1f}%")
            st.metric("Site Slope",    f"{ls['slope_at_site']:.1f}°")
            st.metric("Hazard Level",  f"{ls['hazard_at_site']:.3f}")
            st.metric("Status", "✅ APPROVED" if ls['score'] > 0.3 else "⚠️ MARGINAL")

        with col3:
            st.markdown("**🤖 Rover Path**")
            st.metric("Total Distance", f"{pm['distance_m']:.0f} m")
            st.metric("Path Length",    f"{pm['distance_km']:.3f} km")
            st.metric("Avg Slope",      f"{pm['avg_slope']:.1f}°")
            st.metric("Waypoints",      f"{pm['waypoints']}")

        st.markdown("---")
        st.markdown('<div class="section-header">📄 Download Mission Report</div>', unsafe_allow_html=True)

        os.makedirs("reports", exist_ok=True)

        mission_data = {
            'region': 'Lunar South Pole (Demo)' if st.session_state.get('demo_mode')
                      else 'Chandrayaan-2 Dataset',
            'cpr_threshold':  cpr_threshold,
            'dop_threshold':  dop_threshold,
            'ice':            iv,
            'landing_site':   ls,
            'rover_path':     pm,
            'mission_score':  r['mission_score']
        }

        report_path = "reports/lunar_mission_report.pdf"

        try:
            generate_pdf_report(mission_data, report_path)
            with open(report_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF Mission Report",
                    data=f.read(),
                    file_name="Lunar_Ice_Mission_Report.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Report generation error: {e}")

        col_r, col_c = st.columns(2)
        with col_r:
            if st.button("🔄 Reset Analysis", use_container_width=True):
                for key in ['run_analysis', 'analysis_done', 'demo_mode', 'results']:
                    st.session_state.pop(key, None)
                st.rerun()
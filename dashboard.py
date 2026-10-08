import os
import glob
import sqlite3
import pandas as pd
import streamlit as st
import challan

st.set_page_config(
    page_title="AI Sentinel | Traffic Command Center",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced CSS: Futuristic Neon, Glassmorphism & Keyframe Animations
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Inter:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Background animated subtle glow */
.stApp {
    background: radial-gradient(circle at 15% 20%, rgba(14, 165, 233, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 85% 80%, rgba(168, 85, 247, 0.08) 0%, transparent 40%),
                #0b0f19;
    color: #e2e8f0;
}

/* Animations */
@keyframes slideDown {
    0% { opacity: 0; transform: translateY(-15px); }
    100% { opacity: 1; transform: translateY(0); }
}

@keyframes pulseGlow {
    0% { box-shadow: 0 0 5px rgba(56, 189, 248, 0.2); }
    50% { box-shadow: 0 0 20px rgba(56, 189, 248, 0.5); }
    100% { box-shadow: 0 0 5px rgba(56, 189, 248, 0.2); }
}

@keyframes livePulse {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.15); opacity: 1; }
    100% { transform: scale(0.95); opacity: 0.8; }
}

.header-container {
    animation: slideDown 0.7s ease-out;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 15px;
    margin-bottom: 25px;
}

.brand-title {
    font-family: 'Orbitron', sans-serif;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 32px;
    font-weight: 700;
    margin: 0;
}

.status-dot {
    height: 10px;
    width: 10px;
    background-color: #10b981;
    border-radius: 50%;
    display: inline-block;
    animation: livePulse 1.8s infinite;
    margin-right: 8px;
}

/* Glassmorphism Metric Cards */
.metric-box {
    background: rgba(17, 24, 39, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px;
    backdrop-filter: blur(12px);
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.metric-box:hover {
    transform: translateY(-6px);
    border-color: rgba(56, 189, 248, 0.5);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 15px rgba(56, 189, 248, 0.2);
}

.metric-label {
    color: #94a3b8;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}

.metric-value {
    font-family: 'Orbitron', sans-serif;
    font-size: 36px;
    font-weight: 700;
}

/* Tabs Redesign */
button[data-baseweb="tab"] {
    background-color: transparent !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
}

button[data-baseweb="tab"]:hover {
    color: #38bdf8 !important;
    background: rgba(56, 189, 248, 0.08) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #38bdf8 !important;
    background: rgba(56, 189, 248, 0.15) !important;
    border-bottom: 2px solid #38bdf8 !important;
}

/* Badges */
.badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    display: inline-block;
}
.badge-pending { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
.badge-approved { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
.badge-rejected { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }

/* Expander Cards */
div[data-testid="stExpander"] {
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(15, 23, 42, 0.65) !important;
    backdrop-filter: blur(14px);
    margin-bottom: 14px;
    transition: all 0.3s ease;
}

div[data-testid="stExpander"]:hover {
    border-color: rgba(99, 102, 241, 0.5);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}
</style>
""", unsafe_allow_html=True)

# ----------------- HEADER -----------------
st.markdown("""
<div class="header-container">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 class="brand-title">TRAFFIC SENTINEL AI</h1>
            <p style="color: #64748b; margin: 4px 0 0 0; font-size: 14px;">Next-Gen Computer Vision & ANPR Enforcement Platform</p>
        </div>
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 20px; padding: 6px 16px;">
            <span class="status-dot"></span>
            <span style="color: #34d399; font-size: 13px; font-weight: 600;">ACTIVE INFERENCE NODE</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

conn = sqlite3.connect("violations.db")
try:
    df = pd.read_sql_query("SELECT * FROM violations ORDER BY id DESC", conn)
except Exception:
    df = pd.DataFrame()

# ----------------- TOP METRICS BAR -----------------
total_count = len(df)
pending_count = len(df[df['status'] == 'pending_review']) if not df.empty else 0
approved_count = len(df[df['status'] == 'approved']) if not df.empty else 0
rejected_count = len(df[df['status'] == 'rejected']) if not df.empty else 0

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Total Detections</div><div class="metric-value" style="color:#38bdf8;">{total_count}</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Pending Verification</div><div class="metric-value" style="color:#fbbf24;">{pending_count}</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Approved Challans</div><div class="metric-value" style="color:#34d399;">{approved_count}</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Rejected Flags</div><div class="metric-value" style="color:#f87171;">{rejected_count}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- TABS ARCHITECTURE -----------------
tab_live, tab_desk, tab_analytics, tab_logs = st.tabs([
    "📹 Surveillance Video Feeds",
    "🛡️ Officer Adjudication Desk",
    "📊 Analytics & Violation Trends",
    "📋 Raw Database Logs"
])

# ================= TAB 1: VIDEO PLAYER =================
with tab_live:
    st.markdown("### 🎥 Multi-Camera Surveillance Player")
    video_files = sorted(glob.glob("videos/*.mp4") + glob.glob("videos/*.mkv") + glob.glob("videos/*.webm"))

    if video_files:
        video_options = [os.path.basename(v) for v in video_files]
        col_select, col_meta = st.columns([2, 1])
        
        with col_select:
            selected_video = st.selectbox("Select Traffic Feed:", video_options, key="tab1_feed")
            vpath = os.path.join("videos", selected_video)
            vpath = os.path.join("videos", selected_video)
            try:
                with open(vpath, "rb") as video_file_bytes:
                    st.video(video_file_bytes.read(), format="video/mp4")
            except Exception as e:
                st.error(f"Error loading video stream: {e}")
            
        with col_meta:
            st.markdown(f"""
            <div class="metric-box" style="margin-top: 28px;">
                <h4 style="margin:0; color:#38bdf8;">Node Information</h4>
                <p style="margin: 8px 0; color:#cbd5e1;"><b>Active Source:</b> {selected_video}</p>
                <p style="margin: 8px 0; color:#cbd5e1;"><b>FPS Mode:</b> 30 FPS Stream</p>
                <p style="margin: 8px 0; color:#cbd5e1;"><b>Tracking Model:</b> YOLO11 + ByteTrack</p>
                <p style="margin: 8px 0; color:#cbd5e1;"><b>ANPR Engine:</b> EasyOCR + Positional Regex</p>
            </div>
            """, unsafe_allow_html=True)
            
            if not df.empty and 'video_name' in df.columns:
                feed_df = df[df['video_name'] == selected_video]
                st.metric("Feed Violations Count", len(feed_df))
                st.dataframe(feed_df[['plate', 'violation_type', 'status']], use_container_width=True, height=220)
    else:
        st.warning("No footage found in 'videos/' directory.")

# ================= TAB 2: OFFICER ADJUDICATION DESK =================
with tab_desk:
    st.markdown("### 🛡️ Human-in-the-Loop Case Adjudication")

    filter_col1, filter_col2 = st.columns([1, 2])
    with filter_col1:
        type_options = ["ALL"] + sorted(list(df['violation_type'].unique())) if not df.empty else ["ALL"]
        vfilter = st.selectbox("Filter Offense:", type_options, key="tab2_filter")
    with filter_col2:
        search_plate = st.text_input("🔍 Search License Plate:", "", key="tab2_plate_search").upper()

    display_df = df.copy()
    if not display_df.empty:
        if vfilter != "ALL":
            display_df = display_df[display_df['violation_type'] == vfilter]
        if search_plate:
            display_df = display_df[display_df['plate'].str.contains(search_plate, na=False)]

    if display_df.empty:
        st.info("No cases matching the selected criteria.")
    else:
        for _, row in display_df.iterrows():
            status = str(row['status'])
            badge_cls = "badge-approved" if status == "approved" else ("badge-rejected" if status == "rejected" else "badge-pending")
            img_path = str(row['image_path']) if pd.notna(row['image_path']) else ""
            challan_path = str(row['challan_path']) if pd.notna(row['challan_path']) else ""

            with st.expander(f"Case #{row['id']:04d} | {str(row.get('vehicle_type', 'VEHICLE')).upper()} | {row['plate']} | {row['violation_type']}"):
                c_img, c_info = st.columns([1.2, 1])
                with c_img:
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, caption="Snapshot Photographic Evidence", use_container_width=True)
                    else:
                        st.warning("Evidence image not found on disk.")
                with c_info:
                    st.markdown(f"**Verification Status:** <span class='badge {badge_cls}'>{status.upper()}</span>", unsafe_allow_html=True)
                    st.write(f"**Vehicle Category:** `{str(row.get('vehicle_type', 'vehicle')).upper()}`")
                    st.write(f"**Plate Identifier:** `{row['plate']}`")
                    st.write(f"**Offense Flag:** `{row['violation_type']}`")
                    st.write(f"**Camera Node:** `{str(row.get('video_name', 'CAM01'))}`")
                    st.write(f"**Detection Time:** `{row['ts']}`")

                    st.markdown("<br>", unsafe_allow_html=True)
                    btn1, btn2 = st.columns(2)
                    if btn1.button("✔ Approve & Issue", key=f"t2_app_{row['id']}"):
                        cur = conn.cursor()
                        cur.execute("UPDATE violations SET status='approved' WHERE id=?", (row['id'],))
                        conn.commit()
                        p = challan.make_challan(dict(row))
                        cur.execute("UPDATE violations SET challan_path=? WHERE id=?", (p, row['id']))
                        conn.commit()
                        st.rerun()

                    if btn2.button("✖ Reject Case", key=f"t2_rej_{row['id']}"):
                        cur = conn.cursor()
                        cur.execute("UPDATE violations SET status='rejected' WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()

                    if challan_path and os.path.isfile(challan_path):
                        with open(challan_path, "rb") as f:
                            st.download_button(
                                "📄 Download Official Challan PDF",
                                f,
                                file_name=f"challan_{row['id']:06d}.pdf",
                                key=f"t2_dl_{row['id']}"
                            )

# ================= TAB 3: ANALYTICS & CHARTS =================
with tab_analytics:
    st.markdown("### 📊 Automated Traffic Analytics & Infractions")
    if not df.empty:
        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("#### Violation Breakdown")
            v_counts = df['violation_type'].value_counts()
            st.bar_chart(v_counts)
        with ch2:
            st.markdown("#### Offense by Vehicle Class")
            if 'vehicle_type' in df.columns:
                cls_counts = df['vehicle_type'].value_counts()
                st.bar_chart(cls_counts)
            else:
                st.info("Vehicle classification data will populate on new scans.")
    else:
        st.info("No violation records available to graph.")

# ================= TAB 4: RAW DATABASE LOGS =================
with tab_logs:
    st.markdown("### 📋 System Database Records")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Audit Logs (CSV)", csv_data, "traffic_violations_audit.csv", "text/csv")
    else:
        st.info("Database table is empty.")

conn.close()
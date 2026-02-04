"""
AquaRegWatch Norway - Modern Dashboard UI
A visually polished interface for monitoring Norwegian aquaculture regulations
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models import get_session, Source, Snapshot, Change, Client, Notification

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="AquaRegWatch Norway",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# AquaRegWatch Norway\nNorwegian Aquaculture Regulatory Monitoring"
    }
)

# =============================================================================
# CUSTOM CSS - Modern Dark Theme
# =============================================================================
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Root variables */
    :root {
        --primary: #0ea5e9;
        --primary-dark: #0284c7;
        --secondary: #06b6d4;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --background: #0f172a;
        --surface: #1e293b;
        --surface-light: #334155;
        --text: #f1f5f9;
        --text-muted: #94a3b8;
        --border: #475569;
    }

    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }

    /* Main container */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif !important;
        color: var(--text) !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text);
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, var(--surface) 0%, var(--surface-light) 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    [data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
    }

    /* Custom card styling */
    .custom-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }

    .custom-card h3 {
        margin-top: 0;
        color: #f1f5f9;
        font-size: 1.25rem;
        font-weight: 600;
    }

    /* Alert cards */
    .alert-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .alert-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    }

    .alert-critical { border-left-color: #ef4444; }
    .alert-high { border-left-color: #f59e0b; }
    .alert-medium { border-left-color: #eab308; }
    .alert-low { border-left-color: #10b981; }

    .alert-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 0.5rem;
    }

    .alert-meta {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 1rem;
    }

    .alert-summary {
        color: #cbd5e1;
        line-height: 1.6;
    }

    /* Priority badges */
    .priority-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .priority-critical { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }
    .priority-high { background: rgba(245, 158, 11, 0.2); color: #fcd34d; }
    .priority-medium { background: rgba(234, 179, 8, 0.2); color: #fde047; }
    .priority-low { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }

    /* Status indicators */
    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .status-active { background: #10b981; box-shadow: 0 0 10px #10b981; }
    .status-inactive { background: #ef4444; }
    .status-pending { background: #f59e0b; animation: pulse 2s infinite; }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
    }

    /* Tables */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--surface);
        border-radius: 12px;
        color: var(--text);
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background: var(--surface);
        border-color: var(--border);
        border-radius: 12px;
    }

    /* Text input */
    .stTextInput > div > div > input {
        background: var(--surface);
        border-color: var(--border);
        border-radius: 12px;
        color: var(--text);
    }

    /* Hero section */
    .hero {
        text-align: center;
        padding: 2rem 0 3rem 0;
        margin-bottom: 2rem;
    }

    .hero h1 {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .hero p {
        color: #94a3b8;
        font-size: 1.1rem;
    }

    /* Stats grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
        margin: 2rem 0;
    }

    .stat-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
    }

    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0ea5e9;
    }

    .stat-label {
        color: #94a3b8;
        font-size: 0.875rem;
        margin-top: 0.5rem;
    }

    /* Timeline */
    .timeline-item {
        position: relative;
        padding-left: 2rem;
        padding-bottom: 1.5rem;
        border-left: 2px solid #475569;
    }

    .timeline-item::before {
        content: '';
        position: absolute;
        left: -6px;
        top: 0;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #0ea5e9;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--surface);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DATA LOADING
# =============================================================================
@st.cache_resource
def get_db_session():
    """Get cached database session"""
    return get_session("sqlite:///data/aquaregwatch.db")


def load_data():
    """Load all data from database"""
    try:
        session = get_db_session()
        sources = list(session.query(Source).all())
        changes = list(session.query(Change).order_by(Change.detected_at.desc()).limit(100).all())
        clients = list(session.query(Client).all())
        notifications = list(session.query(Notification).order_by(Notification.created_at.desc()).limit(100).all())

        return {
            "sources": sources,
            "changes": changes,
            "clients": clients,
            "notifications": notifications,
            "session": session
        }
    except Exception as e:
        st.error(f"Database error: {e}")
        return {"sources": [], "changes": [], "clients": [], "notifications": [], "session": None}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_priority_color(priority: str) -> str:
    """Get color for priority level"""
    colors = {
        "critical": "#ef4444",
        "high": "#f59e0b",
        "medium": "#eab308",
        "low": "#10b981"
    }
    return colors.get(priority, "#94a3b8")


def get_priority_emoji(priority: str) -> str:
    """Get emoji for priority level"""
    emojis = {
        "critical": "🚨",
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }
    return emojis.get(priority, "⚪")


def format_time_ago(dt: datetime) -> str:
    """Format datetime as relative time"""
    if not dt:
        return "Never"

    now = datetime.utcnow()
    diff = now - dt

    if diff.days > 30:
        return dt.strftime("%d %b %Y")
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "Just now"


# =============================================================================
# PAGE COMPONENTS
# =============================================================================
def render_sidebar():
    """Render the sidebar navigation"""
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="font-size: 2rem; margin: 0;">🐟</h1>
            <h2 style="font-size: 1.2rem; margin: 0.5rem 0; color: #0ea5e9;">AquaRegWatch</h2>
            <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">Norway Edition</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "📰 Changes", "🌐 Sources", "👥 Clients", "📊 Analytics", "⚙️ Settings"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Quick actions
        st.markdown("### Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("▶️ Check Now", use_container_width=True):
                with st.spinner("Running check..."):
                    os.system("python main.py --check")
                st.success("Done!")
                st.rerun()

        st.markdown("---")

        # Status
        st.markdown("### System Status")
        st.markdown(f"""
        <div style="font-size: 0.85rem;">
            <p><span class="status-dot status-active"></span>Service Active</p>
            <p style="color: #94a3b8;">Last check: {datetime.now().strftime('%H:%M')}</p>
        </div>
        """, unsafe_allow_html=True)

        return page


def render_dashboard(data):
    """Render the main dashboard view"""
    # Hero section
    st.markdown("""
    <div class="hero">
        <h1>🐟 AquaRegWatch</h1>
        <p>Real-time monitoring of Norwegian aquaculture regulations</p>
    </div>
    """, unsafe_allow_html=True)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)

    today_changes = len([c for c in data["changes"] if c.detected_at and c.detected_at.date() == today])
    week_changes = len([c for c in data["changes"] if c.detected_at and c.detected_at > week_ago])
    active_sources = len([s for s in data["sources"] if s.is_active])
    active_clients = len([c for c in data["clients"] if c.is_active])

    with col1:
        st.metric("Changes Today", today_changes, delta=f"+{today_changes}" if today_changes > 0 else None)
    with col2:
        st.metric("This Week", week_changes)
    with col3:
        st.metric("Active Sources", active_sources)
    with col4:
        st.metric("Subscribers", active_clients)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main content grid
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📰 Latest Regulatory Changes")

        recent_changes = data["changes"][:5]

        if not recent_changes:
            st.info("No changes detected yet. Run a check to start monitoring.")

        for change in recent_changes:
            source = next((s for s in data["sources"] if s.id == change.source_id), None)
            source_name = source.name if source else "Unknown"
            priority = change.priority or "medium"

            st.markdown(f"""
            <div class="alert-card alert-{priority}">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div class="alert-title">{get_priority_emoji(priority)} {source_name}</div>
                        <div class="alert-meta">
                            <span class="priority-badge priority-{priority}">{priority}</span>
                            &nbsp;•&nbsp;
                            {format_time_ago(change.detected_at)}
                            &nbsp;•&nbsp;
                            {change.change_percent:.1f}% changed
                        </div>
                    </div>
                </div>
                <div class="alert-summary">
                    {change.summary_no or change.diff_text[:200] + '...' if change.diff_text else 'No summary available'}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        # Priority distribution
        st.markdown("### 📊 By Priority")

        priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for change in data["changes"]:
            p = change.priority or "medium"
            priority_counts[p] = priority_counts.get(p, 0) + 1

        fig = go.Figure(data=[go.Pie(
            labels=list(priority_counts.keys()),
            values=list(priority_counts.values()),
            hole=0.6,
            marker_colors=["#ef4444", "#f59e0b", "#eab308", "#10b981"],
            textinfo='value',
            textfont_size=14,
            textfont_color='white'
        )])

        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(color='#94a3b8')
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=60, l=20, r=20),
            height=280
        )

        st.plotly_chart(fig, use_container_width=True)

        # Source status
        st.markdown("### 🌐 Source Status")

        for source in data["sources"][:6]:
            status_class = "status-active" if source.is_active else "status-inactive"
            last_check = format_time_ago(source.last_checked)

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #334155;">
                <span style="color: #f1f5f9; font-size: 0.9rem;">
                    <span class="status-dot {status_class}"></span>
                    {source.name[:25]}{'...' if len(source.name) > 25 else ''}
                </span>
                <span style="color: #64748b; font-size: 0.8rem;">{last_check}</span>
            </div>
            """, unsafe_allow_html=True)

    # Activity timeline
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📈 Activity Timeline (Last 30 Days)")

    if data["changes"]:
        # Create timeline data
        dates = []
        for change in data["changes"]:
            if change.detected_at and change.detected_at > datetime.utcnow() - timedelta(days=30):
                dates.append(change.detected_at.date())

        if dates:
            date_counts = pd.Series(dates).value_counts().sort_index()

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=date_counts.index,
                y=date_counts.values,
                mode='lines+markers',
                fill='tozeroy',
                fillcolor='rgba(14, 165, 233, 0.1)',
                line=dict(color='#0ea5e9', width=3),
                marker=dict(size=8, color='#0ea5e9'),
                hovertemplate='%{x}<br>%{y} changes<extra></extra>'
            ))

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    showgrid=False,
                    color='#94a3b8',
                    tickformat='%d %b'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(71, 85, 105, 0.3)',
                    color='#94a3b8'
                ),
                margin=dict(t=20, b=40, l=40, r=20),
                height=250,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity data for the last 30 days")
    else:
        st.info("No activity data available yet")


def render_changes(data):
    """Render the changes view"""
    st.markdown("## 📰 Regulatory Changes")
    st.markdown("All detected changes in Norwegian aquaculture regulations")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        categories = list(set(s.category for s in data["sources"] if s.category))
        selected_category = st.selectbox("Category", ["All"] + categories)

    with col2:
        selected_priority = st.selectbox("Priority", ["All", "critical", "high", "medium", "low"])

    with col3:
        date_range = st.selectbox("Time Range", ["Last 24 hours", "Last 7 days", "Last 30 days", "All time"])

    with col4:
        search = st.text_input("Search", placeholder="Search changes...")

    # Filter changes
    filtered_changes = data["changes"]

    if selected_category != "All":
        filtered_changes = [
            c for c in filtered_changes
            if any(s.id == c.source_id and s.category == selected_category for s in data["sources"])
        ]

    if selected_priority != "All":
        filtered_changes = [c for c in filtered_changes if c.priority == selected_priority]

    now = datetime.utcnow()
    if date_range == "Last 24 hours":
        cutoff = now - timedelta(hours=24)
        filtered_changes = [c for c in filtered_changes if c.detected_at and c.detected_at > cutoff]
    elif date_range == "Last 7 days":
        cutoff = now - timedelta(days=7)
        filtered_changes = [c for c in filtered_changes if c.detected_at and c.detected_at > cutoff]
    elif date_range == "Last 30 days":
        cutoff = now - timedelta(days=30)
        filtered_changes = [c for c in filtered_changes if c.detected_at and c.detected_at > cutoff]

    if search:
        search_lower = search.lower()
        filtered_changes = [
            c for c in filtered_changes
            if search_lower in (c.summary_no or "").lower() or search_lower in (c.diff_text or "").lower()
        ]

    st.markdown(f"**{len(filtered_changes)} changes found**")
    st.markdown("---")

    # Display changes
    for change in filtered_changes:
        source = next((s for s in data["sources"] if s.id == change.source_id), None)
        source_name = source.name if source else "Unknown"
        source_url = source.url if source else "#"
        priority = change.priority or "medium"

        with st.expander(f"{get_priority_emoji(priority)} **{source_name}** — {format_time_ago(change.detected_at)}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown("#### 🇳🇴 Norwegian Summary")
                st.markdown(change.summary_no or "_No Norwegian summary available_")

                st.markdown("#### 🇬🇧 English Summary")
                st.markdown(change.summary_en or "_No English summary available_")

                if change.action_items:
                    st.markdown("#### 🎯 Action Items")
                    for item in change.action_items:
                        deadline = f" — _Deadline: {item.get('deadline')}_" if item.get('deadline') else ""
                        priority_badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item.get("priority", ""), "")
                        st.markdown(f"- {priority_badge} {item.get('action')}{deadline}")

            with col2:
                st.markdown("**Details**")
                st.markdown(f"""
                - **Priority:** {priority.upper()}
                - **Category:** {source.category if source else 'Unknown'}
                - **Change %:** {change.change_percent:.1f}%
                - **Detected:** {change.detected_at.strftime('%Y-%m-%d %H:%M') if change.detected_at else 'Unknown'}
                """)

                st.link_button("🔗 View Source", source_url)


def render_sources(data):
    """Render the sources view"""
    st.markdown("## 🌐 Monitored Sources")
    st.markdown("Norwegian government websites being monitored for regulatory changes")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    active = len([s for s in data["sources"] if s.is_active])
    total = len(data["sources"])
    categories = len(set(s.category for s in data["sources"]))

    with col1:
        st.metric("Total Sources", total)
    with col2:
        st.metric("Active", active)
    with col3:
        st.metric("Categories", categories)
    with col4:
        avg_interval = sum(s.check_interval_hours for s in data["sources"]) / max(len(data["sources"]), 1)
        st.metric("Avg Check Interval", f"{avg_interval:.1f}h")

    st.markdown("---")

    # Sources grid
    for source in data["sources"]:
        status_emoji = "🟢" if source.is_active else "🔴"
        last_check = format_time_ago(source.last_checked)
        last_change = format_time_ago(source.last_changed)

        st.markdown(f"""
        <div class="custom-card">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h3 style="margin: 0;">{status_emoji} {source.name}</h3>
                    <p style="color: #64748b; font-size: 0.85rem; margin: 0.5rem 0;">
                        {source.url}
                    </p>
                </div>
                <span class="priority-badge priority-{source.priority}">{source.priority}</span>
            </div>
            <div style="display: flex; gap: 2rem; margin-top: 1rem; color: #94a3b8; font-size: 0.85rem;">
                <span>📁 {source.category}</span>
                <span>⏱️ Every {source.check_interval_hours}h</span>
                <span>🔄 Last check: {last_check}</span>
                <span>📝 Last change: {last_change}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_clients(data):
    """Render the clients view"""
    st.markdown("## 👥 Client Management")
    st.markdown("Manage subscribers and their notification preferences")

    # Stats
    col1, col2, col3, col4 = st.columns(4)

    total = len(data["clients"])
    active = len([c for c in data["clients"] if c.is_active])
    pro = len([c for c in data["clients"] if c.tier in ["pro", "enterprise"]])

    with col1:
        st.metric("Total Clients", total)
    with col2:
        st.metric("Active", active)
    with col3:
        st.metric("Pro/Enterprise", pro)
    with col4:
        # Calculate MRR
        tier_prices = {"basic": 5000, "pro": 15000, "enterprise": 50000}
        mrr = sum(tier_prices.get(c.tier, 0) for c in data["clients"] if c.is_active)
        st.metric("Monthly Revenue", f"{mrr:,} NOK")

    st.markdown("---")

    # Client list
    if data["clients"]:
        for client in data["clients"]:
            tier_colors = {
                "basic": "#64748b",
                "pro": "#0ea5e9",
                "enterprise": "#8b5cf6"
            }
            tier_color = tier_colors.get(client.tier, "#64748b")

            st.markdown(f"""
            <div class="custom-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin: 0;">
                            {'🟢' if client.is_active else '🔴'} {client.name}
                        </h3>
                        <p style="color: #94a3b8; margin: 0.25rem 0;">
                            {client.organization or 'No organization'} • {client.email}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: {tier_color}22; color: {tier_color}; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">
                            {client.tier}
                        </span>
                        <p style="color: #64748b; font-size: 0.8rem; margin: 0.5rem 0 0 0;">
                            {'📧' if client.email_enabled else ''} {'💬' if client.slack_enabled else ''}
                        </p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No clients registered yet")

    # Add client form
    st.markdown("---")
    st.markdown("### ➕ Add New Client")

    with st.form("add_client_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Name *")
            email = st.text_input("Email *")
            organization = st.text_input("Organization")

        with col2:
            tier = st.selectbox("Subscription Tier", ["basic", "pro", "enterprise"])
            slack_webhook = st.text_input("Slack Webhook URL")
            email_enabled = st.checkbox("Email notifications", value=True)

        submitted = st.form_submit_button("Add Client", use_container_width=True)

        if submitted:
            if name and email:
                try:
                    session = get_db_session()
                    new_client = Client(
                        name=name,
                        email=email,
                        organization=organization if organization else None,
                        tier=tier,
                        email_enabled=email_enabled,
                        slack_enabled=bool(slack_webhook),
                        slack_webhook_url=slack_webhook if slack_webhook else None
                    )
                    session.add(new_client)
                    session.commit()
                    st.success(f"✅ Added client: {name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding client: {e}")
            else:
                st.warning("Please fill in required fields (Name and Email)")


def render_analytics(data):
    """Render the analytics view"""
    st.markdown("## 📊 Analytics & Insights")
    st.markdown("Deep dive into regulatory monitoring data")

    # Changes over time
    st.markdown("### Changes Over Time")

    if data["changes"]:
        # Weekly aggregation
        weeks = {}
        for change in data["changes"]:
            if change.detected_at:
                week_start = change.detected_at - timedelta(days=change.detected_at.weekday())
                week_key = week_start.strftime("%Y-%m-%d")
                weeks[week_key] = weeks.get(week_key, 0) + 1

        if weeks:
            df = pd.DataFrame([
                {"Week": k, "Changes": v} for k, v in sorted(weeks.items())
            ])

            fig = px.bar(
                df, x="Week", y="Changes",
                color_discrete_sequence=["#0ea5e9"]
            )

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#94a3b8'),
                yaxis=dict(showgrid=True, gridcolor='rgba(71, 85, 105, 0.3)', color='#94a3b8'),
                margin=dict(t=20, b=40, l=40, r=20),
                height=300
            )

            st.plotly_chart(fig, use_container_width=True)

    # Category breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Changes by Category")

        category_counts = {}
        for change in data["changes"]:
            source = next((s for s in data["sources"] if s.id == change.source_id), None)
            if source:
                cat = source.category
                category_counts[cat] = category_counts.get(cat, 0) + 1

        if category_counts:
            fig = px.bar(
                x=list(category_counts.values()),
                y=list(category_counts.keys()),
                orientation='h',
                color_discrete_sequence=["#06b6d4"]
            )

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(71, 85, 105, 0.3)', color='#94a3b8'),
                yaxis=dict(showgrid=False, color='#94a3b8'),
                margin=dict(t=20, b=40, l=120, r=20),
                height=300
            )

            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Source Activity")

        source_counts = {}
        for change in data["changes"]:
            source = next((s for s in data["sources"] if s.id == change.source_id), None)
            if source:
                source_counts[source.name] = source_counts.get(source.name, 0) + 1

        if source_counts:
            # Get top 5
            top_sources = dict(sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5])

            fig = px.bar(
                x=list(top_sources.values()),
                y=list(top_sources.keys()),
                orientation='h',
                color_discrete_sequence=["#10b981"]
            )

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(71, 85, 105, 0.3)', color='#94a3b8'),
                yaxis=dict(showgrid=False, color='#94a3b8'),
                margin=dict(t=20, b=40, l=150, r=20),
                height=300
            )

            st.plotly_chart(fig, use_container_width=True)

    # Notification stats
    st.markdown("### Notification Performance")

    col1, col2, col3 = st.columns(3)

    sent = len([n for n in data["notifications"] if n.status == "sent"])
    failed = len([n for n in data["notifications"] if n.status == "failed"])
    total = len(data["notifications"])

    with col1:
        st.metric("Total Sent", sent)
    with col2:
        st.metric("Failed", failed)
    with col3:
        success_rate = (sent / max(total, 1)) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")


def render_settings(data):
    """Render the settings view"""
    st.markdown("## ⚙️ Settings")
    st.markdown("Configure your AquaRegWatch instance")

    # API Status
    st.markdown("### 🔑 API Keys Status")

    col1, col2 = st.columns(2)

    with col1:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        sendgrid_key = os.getenv("SENDGRID_API_KEY")

        st.markdown(f"""
        <div class="custom-card">
            <h3>AI Provider</h3>
            <p>{'✅ Anthropic Claude configured' if anthropic_key else '❌ ANTHROPIC_API_KEY not set'}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="custom-card">
            <h3>Email Provider</h3>
            <p>{'✅ SendGrid configured' if sendgrid_key else '❌ SENDGRID_API_KEY not set'}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        openai_key = os.getenv("OPENAI_API_KEY")

        st.markdown(f"""
        <div class="custom-card">
            <h3>Slack Integration</h3>
            <p>{'✅ Webhook configured' if slack_webhook else '⚪ SLACK_WEBHOOK_URL not set (optional)'}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="custom-card">
            <h3>OpenAI (Backup)</h3>
            <p>{'✅ OpenAI configured' if openai_key else '⚪ OPENAI_API_KEY not set (optional)'}</p>
        </div>
        """, unsafe_allow_html=True)

    # Quick actions
    st.markdown("### 🚀 Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Run Full Check", use_container_width=True):
            with st.spinner("Running monitoring cycle..."):
                os.system("python main.py --check")
            st.success("Check complete!")

    with col2:
        if st.button("📧 Send Test Email", use_container_width=True):
            st.info("Test email functionality coming soon")

    with col3:
        if st.button("🧪 Run Tests", use_container_width=True):
            with st.spinner("Running tests..."):
                os.system("python main.py --test")
            st.success("Tests complete!")

    # Database info
    st.markdown("### 💾 Database Statistics")

    stats = {
        "Sources": len(data["sources"]),
        "Changes": len(data["changes"]),
        "Clients": len(data["clients"]),
        "Notifications": len(data["notifications"])
    }

    cols = st.columns(4)
    for i, (key, value) in enumerate(stats.items()):
        with cols[i]:
            st.metric(key, value)


# =============================================================================
# MAIN APP
# =============================================================================
def main():
    # Load data
    data = load_data()

    # Render sidebar and get selected page
    page = render_sidebar()

    # Render selected page
    if page == "🏠 Dashboard":
        render_dashboard(data)
    elif page == "📰 Changes":
        render_changes(data)
    elif page == "🌐 Sources":
        render_sources(data)
    elif page == "👥 Clients":
        render_clients(data)
    elif page == "📊 Analytics":
        render_analytics(data)
    elif page == "⚙️ Settings":
        render_settings(data)


if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Optional PDF parsing
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# --- Page Setup ---
st.set_page_config(page_title="AI ESG Risk Assesment", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    .main { background-color: #0f172a; color: #f1f5f9; }
    h1, h2, h3, h4 { color: #38bdf8; }
    .custom-card {
        background-color: #1e293b;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        margin-bottom: 1rem;
    }
    .block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("AI ESG Risk Assesment")

# --- Mode selector ---
mode = st.radio("Select mode:", ["Use sample data", "Upload ESG report"], horizontal=True)

# --- Default sample ESG data ---
sample_data = {
    "Company": ["Tesla", "Apple", "Microsoft", "Amazon", "Google"],
    "E": [75, 85, 92, 70, 88],
    "S": [65, 90, 88, 60, 80],
    "G": [78, 89, 91, 73, 87],
}
df = pd.DataFrame(sample_data)
df["ESG Score"] = ((df["E"] + df["S"] + df["G"]) / 3).round(1)
df["Risk"] = df["ESG Score"].apply(lambda x: "Low" if x >= 80 else ("Medium" if x >= 60 else "High"))

# --- Handle uploads ---
if mode == "Upload ESG report":
    file = st.file_uploader("Upload CSV or PDF", type=["csv", "pdf"])
    if file is not None:
        st.success(f"File '{file.name}' uploaded successfully!")

        # CSV upload
        if file.name.endswith(".csv"):
            try:
                new_df = pd.read_csv(file)
                new_df.columns = new_df.columns.str.strip()
                # Try to map columns automatically
                col_map = {}
                for col in new_df.columns:
                    c = col.lower()
                    if "env" in c or c == "e": col_map[col] = "E"
                    elif "soc" in c or c == "s": col_map[col] = "S"
                    elif "gov" in c or c == "g": col_map[col] = "G"
                    elif "comp" in c: col_map[col] = "Company"
                new_df = new_df.rename(columns=col_map)

                required = {"Company", "E", "S", "G"}
                if required.issubset(new_df.columns):
                    df = new_df[list(required)].copy()
                    df["ESG Score"] = ((df["E"] + df["S"] + df["G"]) / 3).round(1)
                    df["Risk"] = df["ESG Score"].apply(
                        lambda x: "Low" if x >= 80 else ("Medium" if x >= 60 else "High")
                    )
                    st.success("ESG data loaded from CSV.")
                else:
                    st.error(f"CSV missing required columns: {required - set(new_df.columns)}")

            except Exception as e:
                st.error(f"Error reading CSV: {e}")

        # PDF upload
        elif file.name.endswith(".pdf"):
            if PyPDF2 is None:
                st.error("PDF parsing requires PyPDF2. Install with `pip install PyPDF2`.")
            else:
                try:
                    reader = PyPDF2.PdfReader(file)
                    text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
                    st.info("Extracted text preview (first 500 chars):")
                    st.write(text[:500])

                    # VERY BASIC extraction: look for "Company E S G" patterns
                    rows = []
                    for line in text.splitlines():
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                company = parts[0]
                                e, s, g = float(parts[1]), float(parts[2]), float(parts[3])
                                rows.append([company, e, s, g])
                            except:
                                continue
                    if rows:
                        df = pd.DataFrame(rows, columns=["Company", "E", "S", "G"])
                        df["ESG Score"] = ((df["E"] + df["S"] + df["G"]) / 3).round(1)
                        df["Risk"] = df["ESG Score"].apply(
                            lambda x: "Low" if x >= 80 else ("Medium" if x >= 60 else "High")
                        )
                        st.success("ESG data extracted from PDF.")
                    else:
                        st.error("Could not detect ESG table in PDF. Please use CSV for structured data.")
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")

# --- Main Layout ---
col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("Company Scores")
        st.dataframe(df.style.format({"ESG Score": "{:.1f}"}))
        selected = st.selectbox("Select company", df["Company"])
        row = df[df["Company"] == selected].iloc[0]
        st.metric("Overall ESG Score", f"{row['ESG Score']:.1f}")
        st.write(f"**Risk Level:** {row['Risk']}")
        st.download_button(
            "📥 Download ESG Report",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="esg_scores.csv",
            mime="text/csv"
        )
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader(f"{selected} — ESG Breakdown")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Environmental", "Social", "Governance"],
            y=[row["E"], row["S"], row["G"]],
            marker_color=["#38bdf8", "#818cf8", "#fbbf24"]
        ))
        fig.update_layout(
            yaxis=dict(range=[0,100]),
            title="Component Scores",
            height=400,
            plot_bgcolor="#0f172a",
            paper_bgcolor="#0f172a",
            font=dict(color="#f1f5f9")
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- About Section ---
with st.expander("ℹ About this dashboard"):
    st.write("""
    This AI-driven ESG Risk Dashboard lets you:
    - Explore ESG scores for sample companies
    - Upload your own ESG data as CSV or PDF
    - Automatically view scores, risk levels, and charts
    - Download full ESG reports as CSV
    """)

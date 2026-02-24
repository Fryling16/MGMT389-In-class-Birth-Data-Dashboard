import streamlit as st
import pandas as pd
import plotly.express as px

# STEP 2 — Page Config
st.set_page_config(layout="wide", page_title="Provisional Natality Data Dashboard")

st.title("Provisional Natality Data Dashboard")
st.subheader("Birth Analysis by State and Gender")

# STEP 3 — Load Data
@st.cache_data
def load_data():
    file_path = "Provisional_Natality_2025_CDC.xlsx"
    try:
        # Loading CSV with skiprow if the file has a title header as seen in snippets
        df = pd.read_csv(file_path)
        
        # Check if first row is a header title and reload if necessary
        if "state_of_residence" not in df.columns.str.lower():
             df = pd.read_csv(file_path, skiprows=1)

        # Normalize column names
        df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
        
        # Required logical fields
        required_fields = [
            "state_of_residence", 
            "month", 
            "month_code", 
            "year_code", 
            "sex_of_infant", 
            "births"
        ]
        
        missing = [field for field in required_fields if field not in df.columns]
        
        if missing:
            st.error(f"Missing required columns: {', '.join(missing)}")
            st.write("Actual columns found in file:", df.columns.tolist())
            return None
        
        # Convert births to numeric and drop nulls
        df['births'] = pd.to_numeric(df['births'], errors='coerce')
        df = df.dropna(subset=['births'])
        
        return df

    except FileNotFoundError:
        st.error("Dataset file 'Provisional_Natality_2025_CDC.csv' not found in repository.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return None

df_raw = load_data()

if df_raw is not None:
    # STEP 4 — Sidebar Filters
    st.sidebar.header("Filter Options")

    def create_multiselect(label, options):
        options = sorted([str(x) for x in options])
        selection = st.sidebar.multiselect(label, ["All"] + options, default=["All"])
        return selection

    state_sel = create_multiselect("Select State", df_raw["state_of_residence"].unique())
    month_sel = create_multiselect("Select Month", df_raw["month"].unique())
    gender_sel = create_multiselect("Select Gender", df_raw["sex_of_infant"].unique())

    # STEP 5 — Filtering Logic
    df_filtered = df_raw.copy()

    if "All" not in state_sel:
        df_filtered = df_filtered[df_filtered["state_of_residence"].astype(str).isin(state_sel)]
    
    if "All" not in month_sel:
        df_filtered = df_filtered[df_filtered["month"].astype(str).isin(month_sel)]

    if "All" not in gender_sel:
        df_filtered = df_filtered[df_filtered["sex_of_infant"].astype(str).isin(gender_sel)]

    # STEP 9 — Edge Case: Empty filter result
    if df_filtered.empty:
        st.warning("No data matches the selected filters.")
    else:
        # STEP 6 — Aggregation
        df_agg = df_filtered.groupby(["state_of_residence", "sex_of_infant"], as_index=False)["births"].sum()
        df_agg = df_agg.sort_values("state_of_residence")

        # STEP 7 — Plot
        fig = px.bar(
            df_agg,
            x="state_of_residence",
            y="births",
            color="sex_of_infant",
            title="Total Births by State and Gender",
            labels={"births": "Total Births", "state_of_residence": "State", "sex_of_infant": "Gender"},
            barmode="group",
            template="plotly_white"
        )
        
        fig.update_layout(legend_title_text="Gender")
        st.plotly_chart(fig, use_container_width=True)

        # STEP 8 — Show Filtered Table
        st.write("### Filtered Data Details")
        st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)

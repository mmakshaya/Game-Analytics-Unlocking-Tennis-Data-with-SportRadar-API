import streamlit as st
import pandas as pd
import pymysql

# DB Connection 
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="project"
    )

# Query Execution
def execute_query(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# App Config 
st.set_page_config(
    page_title="Tennis Data Analysis",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar Navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Go to",
    ["🏠 Home",  "🚩 Competitors & Rankings","🎯 Categories & Competitions", "🏟️ Complexes & Venues","📋 Competitor Details Viewer","Queries"]
)

# Home Page 
if page == "🏠 Home":
    st.title("🎾 Tennis Data Dashboard 🥎")
    st.write("Welcome to the tennis data analysis app!")

    st.header("📊 Dashboard Summary")

    # Query 1: Overall Summary
    summary_query = """
        SELECT 
            COUNT(DISTINCT cr.competitor_id) AS total_competitors,
            COUNT(DISTINCT c.country) AS total_countries,
            MAX(cr.points) AS highest_points
        FROM competitor_rankings cr
        JOIN competitors c ON cr.competitor_id = c.competitor_id
    """
    summary_df = execute_query(summary_query)

    # Query 2: Top Player
    top_player_query = """
        SELECT 
            c.name AS top_player,
            c.country_name AS top_country,
            cr.rank AS top_rank
        FROM competitor_rankings cr
        JOIN competitors c ON cr.competitor_id = c.competitor_id
        WHERE cr.points = (
            SELECT MAX(points) FROM competitor_rankings
        )
        
    """
    top_df = execute_query(top_player_query)

    # Show Summary Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("🎾 Total Competitors", int(summary_df["total_competitors"][0]))
    col2.metric("🌍 Countries Represented", int(summary_df["total_countries"][0]))
    col3.metric("⭐ Highest Points", int(summary_df["highest_points"][0]))

    # Show Top Player Info
    st.subheader("🏅 Top Player")
    st.markdown(f"""
    - **Name:** {top_df['top_player'][0]}
    - **Country:** {top_df['top_country'][0]}
    - **Rank:** #{top_df['top_rank'][0]}
    """)

    st.markdown("""
        ---
        ✅ Use the sidebar to explore:
        - Tournament categories and competitions  
        - Complexes and venues  
        - Competitor rankings and statistics 
    """)

# Page 1: Categories & Competitions 
elif page == "🎯 Categories & Competitions":
    st.header("🎯 Categories & Competitions")

    # Load full joined data
    query = """
        SELECT 
            c.category_id,
            c.competition_id,
            c.competition_name,
            c.type,
            c.gender,
            cat.category_name,
            c.parent_id 
        FROM categories cat
        JOIN competitions c ON c.category_id = cat.category_id
        ORDER BY c.category_id
    """
    joined_df = execute_query(query)

    # Sidebar Filters (independent)
    with st.sidebar:
        st.subheader("🔍 Filter Competitions")

        # Text input for competition name
        input_name = st.text_input("📛 Competition Name (search by text)")

        # Get full unique values independently for each filter
        gender_options = sorted(joined_df["gender"].dropna().unique())
        type_options = sorted(joined_df["type"].dropna().unique())

        # Independent dropdowns with "All" option for both
        selected_gender = st.selectbox("⚥ Gender", options=["All"] + gender_options)
        selected_type = st.selectbox("📂 Type", options=["All"] + type_options)

    # Apply Filters
    filtered_df = joined_df.copy()

    if input_name:
        filtered_df = filtered_df[filtered_df["competition_name"].str.contains(input_name, case=False)]

    if selected_gender != "All":
        filtered_df = filtered_df[filtered_df["gender"] == selected_gender]

    if selected_type != "All":
        filtered_df = filtered_df[filtered_df["type"] == selected_type]

    # Display Filtered Table
    st.subheader("📋 Filtered Competitions")
    st.dataframe(filtered_df, use_container_width=True)
    
    # Competitor Detail Viewer
elif page == "📋 Competitor Details Viewer":
    st.header("📋 Competitor Details Viewer")

    # Load competitor data
    query = """
        SELECT 
            r.competitor_id,
            r.rank,
            r.points,
            r.movement,
            r.competitions_played,
            c.name AS name,
            c.country_name AS country,
            c.abbreviation
        FROM competitor_rankings r
        JOIN competitors c ON r.competitor_id = c.competitor_id
        ORDER BY r.rank ASC
    """
    competitor_df = execute_query(query)

    # Check if data exists
    if not competitor_df.empty:
        # Select competitor from dropdown
        selected_name = st.selectbox("Select a Competitor", competitor_df["name"].unique())

        # Get details for selected competitor
        competitor_details = competitor_df[competitor_df["name"] == selected_name]

        if not competitor_details.empty:
            st.markdown("### 🧾 Competitor Details")

            col1, col2 = st.columns(2)
            col1.metric("Rank", int(competitor_details["rank"].values[0]))
            col2.metric("Movement", int(competitor_details["movement"].values[0]))

            col3, col4 = st.columns(2)
            col3.metric("Competitions Played", int(competitor_details["competitions_played"].values[0]))
            col4.metric("Country", competitor_details["country"].values[0])

            st.markdown(f"**Abbreviation:** {competitor_details['abbreviation'].values[0]}")
            st.markdown(f"**Competitor ID:** `{competitor_details['competitor_id'].values[0]}`")
    else:
        st.info("No competitor data available.")
    
    # Page 2: Complexes & Venues 
elif page == "🏟️ Complexes & Venues":
    st.header("🏟️ Complexes & Venues")

    # Load full data
    complex_query = "SELECT * FROM complexes"
    df_complex = execute_query(complex_query)

    venue_query = "SELECT * FROM venues"
    df_venue = execute_query(venue_query)


    # Sidebar Filters
    with st.sidebar:
        st.subheader("🔍 Filter Specific Details")

        complex_options = ["All"] + sorted(df_complex["complex_name"].dropna().unique())
        selected_complex = st.selectbox("🏢 Select Complex", complex_options)

        venue_options = ["All"] + sorted(df_venue["venue_name"].dropna().unique())
        selected_venue = st.selectbox("🎾 Select Venue", venue_options)

    # Merge on complex_id (ensure both tables have that column)
    if "complex_id" in df_complex.columns and "complex_id" in df_venue.columns:
        combined_df = df_venue.merge(
            df_complex,
            how="left",
            on="complex_id",
            suffixes=("_venue", "_complex")
        )

        # Apply Filters
        filtered_df = combined_df.copy()
        if selected_complex != "All":
            filtered_df = filtered_df[filtered_df["complex_name"] == selected_complex]
        if selected_venue != "All":
            filtered_df = filtered_df[filtered_df["venue_name"] == selected_venue]

        # Display Filtered Results
        st.subheader("📋 Filtered Result (Venue + Complex)")
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.error("❌ `complex_id` not found in one or both tables. Please check your schema.")

    # Show original tables for reference
    st.subheader("🏢 All Complexes")
    st.dataframe(df_complex, use_container_width=True)

    st.subheader("🎾 All Venues")
    st.dataframe(df_venue, use_container_width=True)

# Page 3: Competitors & Rankings 
elif page == "🚩 Competitors & Rankings":
    st.header("🚩 Competitors & Rankings")

    # Load data
    query = """
        SELECT 
            r.competitor_id,
            r.rank,
            r.points,
            r.movement,
            r.competitions_played,
            c.name AS name,
            c.country_name AS country,
            c.abbreviation
        FROM competitor_rankings r
        JOIN competitors c ON r.competitor_id = c.competitor_id
        ORDER BY r.rank ASC
    """
    competitor_df = execute_query(query)

    # Sidebar Filters
    st.sidebar.subheader("🔍 Search & Filter")

    search_name = st.sidebar.text_input("🧾 Search by Name")
    country_filter = st.sidebar.multiselect("🌎 Filter by Country", options=competitor_df["country"].unique())

    # Rank Range Slider
    rank_min = int(competitor_df["rank"].min())
    rank_max = int(competitor_df["rank"].max())
    rank_range = st.sidebar.slider("🥇 Filter by Rank", min_value=rank_min, max_value=rank_max, value=(rank_min, rank_max))


    # Apply Filters
    filtered_df = competitor_df.copy()
    if search_name:
        filtered_df = filtered_df[filtered_df["name"].str.contains(search_name, case=False)]
    if country_filter:
        filtered_df = filtered_df[filtered_df["country"].isin(country_filter)]
    filtered_df = filtered_df[
        (filtered_df["rank"] >= rank_range[0]) & 
        (filtered_df["rank"] <= rank_range[1]) 
    ]

    # Show Filtered Results
    st.subheader("🎯 Filtered Competitors")
    st.dataframe(filtered_df, use_container_width=True)


# Page 3: Query
elif page == "Queries":
    st.title("📋 Common FAQ")

    queries = {
        "1. all competitions along with their category name": "SELECT c.competition_id,c.competition_name,cat.category_name FROM competitions c JOIN categories cat ON c.category_id = cat.category_id",
        "2. Count the number of competitions in each category": "SELECT c.category_id, cat.category_name, COUNT(*) AS competition_count FROM competitions c JOIN categories cat ON c.category_id = cat.category_id GROUP BY cat.category_name ORDER BY competition_count DESC",
        "3. Find all competitions of type 'doubles'": "SELECT competition_id, competition_name, type FROM competitions WHERE type = 'doubles'",
        "4. competitions with no parent (top-level competitions)": "SELECT competition_id, competition_name, type, gender, category_id FROM competitions WHERE parent_id IS NULL",
        "5. all venues along with their associated complex name":" SELECT c.complex_name,v.venue_name FROM complexes c JOIN venues v ON c.complex_id = v.complex_id",
        "6. Count the number of venues in each complex":" SELECT c.complex_id,c.complex_name,COUNT(v.venue_id) AS venue_count FROM Complexes c JOIN Venues v ON c.complex_id = v.complex_id GROUP BY c.complex_name",
        "7. Identify all venues and their timezones": "SELECT venue_id, venue_name, timezone FROM Venues",
        "8. complexes that have more than one venue":"SELECT c.complex_id, c.complex_name,COUNT(v.venue_id) AS venue_count FROM Complexes c JOIN Venues v ON c.complex_id = v.complex_id GROUP BY c.complex_name HAVING venue_count > 1",
        "9. List venues grouped by country":"SELECT venue_id, venue_name,country_name FROM Venues Group by country_name",
        "10. all competitors with their rank and points":"SELECT rank,points,competitor_id FROM competitor_rankings",
        "11. competitors ranked in the top 5":"SELECT cr.rank,cr.competitor_id,cr.point FROM competitor_rankings cr JOIN competitors c ON cr.competitor_id = c.competitor_id WHERE cr.rank<=5 order by cr.rank",
        "12. competitors with no rank movement":"SELECT cr.rank,c.name,cr.competitor_id,cr.movement,cr.points FROM competitor_rankings cr JOIN competitors c ON cr.competitor_id = c.competitor_id WHERE cr.movement = 0",
        "13. Count the number of competitors per country":"SELECT country,COUNT(*) AS number_of_competitors FROM competitors GROUP BY country",
        "14. competitors with the highest points in the current week":"SELECT cr.rank,cr.points,c.name,cr.competitor_id,c.country FROM competitor_rankings cr JOIN competitors c ON cr.competitor_id = c.competitor_id WHERE cr.points = (SELECT MAX(points) FROM competitor_rankings)"
    }

    selected_query = st.selectbox("Commonly Asked Questions", list(queries.keys()))
    query_result = execute_query(queries[selected_query])  

    st.write("### Query Result:")
    st.dataframe(query_result, use_container_width=True)

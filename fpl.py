import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Run with:
# streamlit run fpl.py

# ---------------------------
# Fetch FPL data
# ---------------------------
@st.cache_data
def fetch_fpl_data():
    cols_to_remove = [
        "can_transact", "can_select", "chance_of_playing_next_round", "chance_of_playing_this_round",
        "code", "cost_change_event", "cost_change_event_fall", "cost_change_start", "cost_change_start_fall",
        "dreamteam_count", "ep_next", "ep_this", "event_point", "first_name", "id", "in_dreamteam", "news",
        "news_added", "photo", "removed", "second_name", "special", "squad_number", "status", "region",
        "team_join_date", "birth_date", "has_temporary_code", "opta_code", "influence_rank", "influence_rank_type",
        "creativity_rank", "creativity_rank_type", "threat_rank", "threat_rank_type", "ict_index_rank",
        "ict_index_rank_type", "corners_and_indirect_freekicks_order", "corners_and_indirect_freekicks_text",
        "direct_freekicks_order", "direct_freekicks_text", "penalties_order", "penalties_text", "now_cost_rank",
        "now_cost_rank_type", "form_rank", "form_rank_type", "points_per_game_rank", "points_per_game_rank_type",
        "selected_rank", "selected_rank_type", "id_team", "id_pos"
    ]

    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    data = response.json()
    
    players = pd.DataFrame(data['elements'])
    teams = pd.DataFrame(data['teams'])
    positions = pd.DataFrame(data['element_types'])
    
    players = (
        players
        .merge(teams[['id', 'name']], left_on='team', right_on='id', suffixes=('', '_team'))
        .merge(positions[['id', 'singular_name_short']], left_on='element_type', right_on='id', suffixes=('', '_pos'))
        .rename(columns={'name': 'team_name', 'singular_name_short': 'position'})
    
    )

    players.drop(cols_to_remove, axis=1, errors="ignore", inplace=True)

    for i in range(len(players.columns)):
        new_name = players.columns[i].replace('_', ' ').capitalize()
        players.rename(columns={players.columns[i]: new_name}, inplace=True)

    players = players[players["Minutes"] >= 300]

    return players

# ---------------------------
# Main App
# ---------------------------
st.set_page_config(layout="wide")
# st.title("⚽ FPL data plotting tool")

df = fetch_fpl_data()

# Convert numeric-like object columns to numeric
for col in df.columns:
    if df[col].dtype == object:
        try:
            df[col] = pd.to_numeric(df[col])
        except ValueError:
            pass  # leave as string if conversion fails

# Separate column lists
numeric_cols = sorted(df.select_dtypes(include=['number']).columns)  # for X and Y
all_cols = list(df.columns)  # for color

# Layout
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("⚙️ FPL plot settings")
    x_col = st.selectbox("X-axis", numeric_cols, index=numeric_cols.index("Now cost"))
    y_col = st.selectbox("Y-axis", numeric_cols, index=numeric_cols.index("Total points"))
    color_col = "Element type"
    size_col = None #st.selectbox("Size by", [None] + numeric_cols, index=0)
    
    positions = sorted(df['Position'].unique())
    selected_positions = st.multiselect("Filter by position", positions, default=positions)

# Fixed color map for positions
position_colors = {
    'GKP': 'blue',
    'DEF': 'green',
    'MID': 'orange',
    'FWD': 'red'
}

# Apply colors

with col2:
    # Filter
    df_filtered = df[df['Position'].isin(selected_positions)]
    point_colors = df_filtered['Position'].map(position_colors)

    fig, ax = plt.subplots(figsize=(12, 8))

    # Handle color mapping
    if color_col:
        categories = df_filtered[color_col].astype('category')
        scatter = ax.scatter(
            df_filtered[x_col],
            df_filtered[y_col],
            c=point_colors,
            s=df_filtered[size_col] if size_col else 50,
            cmap='tab20',
            alpha=0.7
        )
        # Legend for categories
        from matplotlib.patches import Patch
        legend_elements = [Patch(color=color, label=pos) for pos, color in position_colors.items() if pos in selected_positions]
        ax.legend(handles=legend_elements, title="Position", bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        scatter = ax.scatter(
            df_filtered[x_col],
            df_filtered[y_col],
            c='blue',
            s=df_filtered[size_col] if size_col else 50,
            alpha=0.7
        )

    # Add annotations
    for _, row in df_filtered.iterrows():
        ax.annotate(
            row['Web name'],
            (row[x_col], row[y_col]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8,
            alpha=0.7
        )

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(f"{y_col} vs {x_col}")
    ax.grid(True)

    st.pyplot(fig)

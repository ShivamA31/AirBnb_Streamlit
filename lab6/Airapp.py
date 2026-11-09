from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Airbnb Analytics", page_icon="🏠", layout="wide")

st.title("Airbnb Listing, Pricing and Host Analytics")
st.write("Explore Airbnb prices, ratings, reviews and listing locations.")

# Load the CSV kept in the same folder as this Python file.
try:
    df = pd.read_csv(Path(__file__).parent / "airbnb.csv")
except FileNotFoundError:
    st.error("airbnb.csv is missing. Keep it in the same folder as Airapp.py.")
    st.stop()

# Convert the fields used in the charts to numbers.
for column in ["price", "rating", "reviews", "bedrooms", "guests"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(subset=["price", "country"])
df["country"] = df["country"].str.strip()

# Sidebar filters
st.sidebar.header("Filters")
countries = sorted(df["country"].dropna().unique())
popular_countries = df["country"].value_counts().head(5).index.tolist()
selected_countries = st.sidebar.multiselect(
    "Choose countries", countries, default=popular_countries
)

bedrooms = sorted(df["bedrooms"].dropna().unique())
popular_bedrooms = df["bedrooms"].value_counts().head(5).sort_index().index.tolist()
selected_bedrooms = st.sidebar.multiselect(
    "Choose bedrooms", bedrooms, default=popular_bedrooms
)

# Exclude the most extreme 1% by default so the price charts are readable.
max_price = float(df["price"].quantile(0.99))
price_range = st.sidebar.slider(
    "Price range",
    float(df["price"].min()),
    max_price,
    (float(df["price"].min()), max_price),
)

min_rating = st.sidebar.slider("Minimum rating", 0.0, 5.0, 0.0, 0.1)

filtered = df[
    (df["country"].isin(selected_countries))
    & (df["bedrooms"].isin(selected_bedrooms))
    & (df["price"].between(price_range[0], price_range[1]))
    & (df["rating"].isna() | (df["rating"] >= min_rating))
]

if filtered.empty:
    st.warning("No listings match these filters. Try changing your selections.")
    st.stop()

# Separate the app into assignment sections.
overview, analysis, charts, insights = st.tabs(
    ["Dataset Overview", "Data Analysis", "Visualizations", "Insights"]
)

with overview:
    st.subheader("Key numbers")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total listings", f"{len(filtered):,}")
    c2.metric("Total price", f"{filtered['price'].sum():,.0f}")
    c3.metric("Average price", f"{filtered['price'].mean():,.0f}")
    c4.metric("Average rating", f"{filtered['rating'].mean():.2f}")

    st.subheader("Listings by country")
    country_counts = filtered.groupby("country").size().reset_index(name="Listings")
    country_counts = country_counts.sort_values("Listings", ascending=False)
    st.dataframe(country_counts, hide_index=True, use_container_width=True)

    with st.expander("Show filtered dataset"):
        st.dataframe(filtered, use_container_width=True)

with analysis:
    st.subheader("Summary by country")
    summary = filtered.groupby("country").agg(
        Listings=("price", "count"),
        Average_Price=("price", "mean"),
        Average_Rating=("rating", "mean"),
        Total_Reviews=("reviews", "sum"),
    ).round(2)
    st.dataframe(summary, use_container_width=True)

    st.subheader("Top hosts by listing count")
    top_hosts = filtered.groupby("host_name").size().sort_values(ascending=False).head(10)
    st.dataframe(top_hosts.rename("Listings").reset_index(), hide_index=True, use_container_width=True)

with charts:
    left, right = st.columns(2)

    with left:
        st.subheader("Bar chart: listings by country")
        country_counts = filtered.groupby("country").size().reset_index(name="Listings")
        country_counts = country_counts.sort_values("Listings", ascending=False).head(10)
        bar = px.bar(
            country_counts,
            x="country",
            y="Listings",
            title="Top 10 Countries by Listing Count",
            labels={"country": "Country", "Listings": "Number of listings"},
        )
        st.plotly_chart(bar, use_container_width=True)

    with right:
        st.subheader("Line chart: price by bedrooms")
        bedroom_prices = filtered.groupby("bedrooms")["price"].mean().reset_index()
        line = px.line(
            bedroom_prices,
            x="bedrooms",
            y="price",
            markers=True,
            title="Average Price by Number of Bedrooms",
            labels={"bedrooms": "Bedrooms", "price": "Average price"},
        )
        st.plotly_chart(line, use_container_width=True)

    st.subheader("Scatter plot: price and rating")
    scatter = px.scatter(
        filtered.dropna(subset=["rating"]),
        x="rating",
        y="price",
        color="country",
        title="Price Compared with Rating",
        labels={"rating": "Rating", "price": "Price", "country": "Country"},
    )
    st.plotly_chart(scatter, use_container_width=True)

with insights:
    st.subheader("What the filtered data shows")
    st.write(f"There are **{len(filtered):,} listings** in the current selection.")
    st.write(f"The average listing price is **{filtered['price'].mean():,.0f}**.")

    country_prices = filtered.groupby("country")["price"].mean()
    if not country_prices.empty:
        st.info(
            f"The highest average price is in **{country_prices.idxmax()}** "
            f"({country_prices.max():,.0f})."
        )

    price_rating_correlation = filtered[["price", "rating"]].corr().iloc[0, 1]
    st.write(
        f"The correlation between price and rating is "
        f"**{price_rating_correlation:.2f}**. A correlation shows a relationship, "
        "but does not prove that one causes the other."
    )

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import pymysql

# Database connection using SQLAlchemy
def get_connection():
    username = "8hFDjrykeNW5E7u.root"
    password = "tlaUjhwvLvFxpd9v"
    host = "gateway01.us-west-2.prod.aws.tidbcloud.com"
    port = 4000
    database = "test"

    engine = create_engine(
        f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}",
        connect_args={"ssl_disabled": False}
    )
    return engine.connect()

# Home Page
def home_page(connection):
    st.title("📈 Stocks Analysis Dashboard")
    st.markdown("""
        Welcome to the **Streamlit-based stock analysis dashboard**!
        
        📌Navigate through the sidebar to explore:
        - **Volatility Analysis**
        - **Cumulative Returns**
        - **Sector Performance**
        - **Stock Price Correlations**
        - **Top Gainers and Losers**
    """)

    # Top 10 Green Stocks
    st.subheader("🌿 Top 10 Green Stocks (Highest Yearly Returns)")
    green_data = {
        'symbol': ['TRENT', 'BEL', 'M&M', 'BAJAJ-AUTO', 'BHARTIARTL', 'POWERGRID', 'BPCL', 'HEROMOTOCO', 'SUNPHARMA', 'HCLTECH'],
        'yearly_return': [223.09, 101.76, 95.98, 89.01, 69.60, 68.85, 67.48, 58.98, 57.28, 53.26]
    }
    green_df = pd.DataFrame(green_data)
    st.dataframe(green_df)

    # Top 5 Loss Stocks
    st.subheader("📉 Top 5 Loss Stocks")
    red_data = {
        'symbol': ['INDUSINDBK', 'ASIANPAINT', 'BAJFINANCE', 'ADANIENT', 'HINDUNILVR'],
        'yearly_return': [-30.46, -21.94, -16.11, -6.67, -0.96]
    }
    red_df = pd.DataFrame(red_data)
    st.dataframe(red_df)

    # Market Summary
    st.subheader("📊 Market Summary")
    st.markdown("""
    **✅ Green Stocks:** 45  
    **❌ Red Stocks:** 5  
    **💰 Average Price Across All Stocks:** ₹2,449.42  
    **🛆 Average Volume Across All Stocks:** 6,833,475  
    """)

# Volatility Analysis
def volatility_analysis(connection):
    st.title("📊 1. Volatility Analysis")
    try:
        df = pd.read_sql("SELECT * FROM top_10_volatile_stocks", connection)
        df.columns = df.columns.str.strip()
        st.subheader("Top 10 Most Volatile Stocks")
        st.dataframe(df)

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x='Ticker', y='Volatility', data=df, palette='viridis', ax=ax)
        ax.set_title('Top 10 Most Volatile Stocks')
        ax.set_xlabel('Stock')
        ax.set_ylabel('Volatility (Std Dev of Returns)')
        ax.tick_params(axis='x', rotation=45)

        for bar in ax.patches:
            height = bar.get_height()
            ax.annotate(f"{height:.4f}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

        st.pyplot(fig)
        plt.clf()
    except Exception as e:
        st.error(f"Error loading or plotting volatility data: {e}")

# Cumulative Returns
def cumulative_return(connection):
    st.title("📈 Cumulative Return for Top 5 Performing Stocks")
    try:
        df = pd.read_sql("SELECT * FROM top5_cumulative_returns", connection)
        df.columns = df.columns.str.strip()
        st.write("Columns in cumulative return df:", df.columns.tolist())

        if 'date' in df.columns and 'Cumulative_Return' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.lineplot(data=df, x="date", y="Cumulative_Return", hue="Ticker", ax=ax, marker='o')
            ax.set_title("Top 5 Tickers - Cumulative Return Over Time")
            ax.set_ylabel("Cumulative Return")
            ax.set_xlabel("Date")
            ax.grid(True)
            st.pyplot(fig)
        else:
            st.error("Missing 'date' or 'Cumulative_Return' columns in the data.")
    except Exception as e:
        st.error(f"Error loading or plotting cumulative return data: {e}")

# Sector Performance
def sector_performance(connection):
    st.title("🏢 3. Sector-wise Performance")
    try:
        df_sector = pd.read_sql("SELECT * FROM Average_Yearly_Return_By_Sector", connection)
        df_sector.columns = df_sector.columns.str.strip()

        if 'Sector' in df_sector.columns and 'Avg_Yearly_Return' in df_sector.columns:
            df_sector['Avg_Yearly_Return'] = pd.to_numeric(df_sector['Avg_Yearly_Return'], errors='coerce')
            df_sector = df_sector.sort_values(by='Avg_Yearly_Return', ascending=False)
            st.subheader("📊 Average Return by Sector")
            df_display = df_sector.copy()
            df_display['Avg_Yearly_Return'] = df_display['Avg_Yearly_Return'].map('{:.2f}%'.format)
            st.dataframe(df_display)

            fig, ax = plt.subplots(figsize=(12, 6))
            sns.barplot(data=df_sector, x='Sector', y='Avg_Yearly_Return', palette='Set2', ax=ax)
            ax.set_title('Average Yearly Return by Sector')
            ax.set_xlabel('Sector')
            ax.set_ylabel('Return (%)')
            ax.tick_params(axis='x', rotation=45)
            ax.axhline(0, color='gray', linestyle='--', linewidth=1)
            for p in ax.patches:
                ax.annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='bottom', fontsize=9)
            st.pyplot(fig)
            plt.clf()

            df_stocks = pd.read_sql("SELECT * FROM Ticker_Sector_YearlyReturns", connection)
            df_stocks.columns = df_stocks.columns.str.strip()
            df_stocks['Avg_Yearly_Return'] = pd.to_numeric(df_stocks['Avg_Yearly_Return'], errors='coerce')
            st.subheader("🔍 Explore Stock Contributions by Sector")

            for sector in df_sector['Sector']:
                with st.expander(f"📂 {sector} - Show Contributing Stocks"):
                    df_filtered = df_stocks[df_stocks['Sector'] == sector].sort_values(by='Avg_Yearly_Return', ascending=False)
                    df_filtered_display = df_filtered.copy()
                    df_filtered_display['Avg_Yearly_Return'] = df_filtered_display['Avg_Yearly_Return'].map('{:.2f}%'.format)
                    st.dataframe(df_filtered_display.reset_index(drop=True), use_container_width=True)
        else:
            st.error("Missing 'Sector' or 'Avg_Yearly_Return' columns in the data.")
    except Exception as e:
        st.error(f"Error loading sector performance data: {e}")

# Stock Correlation
def stock_correlation(connection):
    st.title("🔗 4. Stock Price Correlation")
    try:
        df = pd.read_sql("SELECT * FROM Stock_Correlation_Matrix", connection)
        df.set_index(df.columns[0], inplace=True)
        df.columns.name = 'Ticker2'
        df.index.name = 'Ticker1'

        st.subheader("📊 Correlation Heatmap")
        fig, ax = plt.subplots(figsize=(22, 20))
        sns.heatmap(df, cmap="coolwarm", annot=True, fmt=".2f", ax=ax)
        ax.set_title("Stock Correlation Matrix")
        st.pyplot(fig)

        corr_pairs = df.stack().reset_index().rename(columns={0: 'Correlation'})
        corr_pairs = corr_pairs[corr_pairs['Ticker1'] != corr_pairs['Ticker2']]
        corr_pairs['Pair'] = corr_pairs.apply(lambda row: tuple(sorted([row['Ticker1'], row['Ticker2']])), axis=1)
        corr_pairs = corr_pairs.drop_duplicates(subset='Pair').drop(columns='Pair')

        strong_corr = corr_pairs[corr_pairs['Correlation'] >= 0.8].sort_values(by='Correlation', ascending=False)
        weak_corr = corr_pairs[corr_pairs['Correlation'] <= 0.2].sort_values(by='Correlation')

        st.subheader("🔍 Explore Correlation Details")
        with st.expander("💪 Strong Correlations (≥ 0.80)"):
            st.dataframe(strong_corr.reset_index(drop=True), use_container_width=True)
        with st.expander("🧙‍♂️ Weak Correlations (≤ 0.20)"):
            st.dataframe(weak_corr.reset_index(drop=True), use_container_width=True)
    except Exception as e:
        st.error(f"Error loading or plotting correlation data: {e}")

# Gainers & Losers
def gainers_losers(connection):
    st.title("📅 Monthly Top 5 Gainers & Losers")
    try:
        df = pd.read_sql("SELECT * FROM Monthly_Top_Gainers_Losers", connection)
        df.columns = df.columns.str.strip()
        df['Month'] = pd.to_datetime(df['Month'], format="%b %Y")
        months = sorted(df['Month'].dt.to_period("M").unique())

        for month in months:
            st.subheader(f"📊 {month.strftime('%B %Y')} - Top Gainers and Losers")
            month_data = df[df['Month'].dt.to_period("M") == month]
            gainers = month_data[month_data['Type'] == 'Gainer']
            losers = month_data[month_data['Type'] == 'Loser']

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Top 5 Gainers**")
                fig, ax = plt.subplots(figsize=(6, 4))
                sns.barplot(data=gainers, x="Ticker", y="Return (%)", ax=ax, palette="Greens_d")
                ax.set_title("Gainers")
                ax.set_ylim(-100, 100)
                for bar in ax.patches:
                    height = bar.get_height()
                    ax.annotate(f"{height:.2f}%", 
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 5),
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9)
                st.pyplot(fig)

            with col2:
                st.markdown("**Top 5 Losers**")
                fig, ax = plt.subplots(figsize=(6, 4))
                sns.barplot(data=losers, x="Ticker", y="Return (%)", ax=ax, palette="Reds_d")
                ax.set_title("Losers")
                ax.set_ylim(-100, 100)
                for bar in ax.patches:
                    height = bar.get_height()
                    ax.annotate(f"{height:.2f}%", 
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 5),
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9)
                st.pyplot(fig)
    except Exception as e:
        st.error(f"Error loading or plotting gainers/losers data: {e}")

# Main App
def main():
    st.set_page_config(page_title="Stock Dashboard", layout="wide")
    st.sidebar.title("📌 Navigation")
    pages = {
        "Home": home_page,
        "Volatility Analysis": volatility_analysis,
        "Cumulative Returns": cumulative_return,
        "Sector Performance": sector_performance,
        "Stock Correlation": stock_correlation,
        "Gainers & Losers": gainers_losers,
        # "Price History": price_history,  # Disabled - No daily price data available
    }

    selection = st.sidebar.radio("Go to", list(pages.keys()))
    connection = get_connection()
    try:
        pages[selection](connection)
    finally:
        connection.close()

if __name__ == "__main__":
    main()

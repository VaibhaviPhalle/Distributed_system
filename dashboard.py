import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Page Configuration: Force wide mode to use all available space
st.set_page_config(page_title="Rate Limiter Metrics", layout="wide")

st.title("🚀 Rate Limiter Performance Monitor")
st.markdown("---")

# 2. Data Loader: Robust loading for your Locust output
def load_data():
    csv_path = "results/stats_stats.csv" # Ensure your Locust run saves to this path
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        # Fallback Mock Data for demo purposes if CSV isn't found
        return pd.DataFrame({
            'Name': ['/api/data', '/api/user', '/api/login', '/api/policies'],
            'Request Count': [1500, 800, 300, 50],
            'Failure Count': [5, 2, 0, 0],
            'Average Response Time': [2.5, 4.2, 12.0, 8.5],
            'Median Response Time': [2.0, 3.5, 10.0, 7.0]
        })

df = load_data()

# 3. KPI Metrics (Top Row)
col1, col2, col3 = st.columns(3)
col1.metric("Total Requests", df['Request Count'].sum())
col2.metric("Total Failures", df['Failure Count'].sum())
col3.metric("Avg Latency", f"{round(df['Average Response Time'].mean(), 2)} ms")

# 4. Stacked Bar Chart (Traffic Distribution)
st.subheader("Traffic Distribution: Requests vs. Failures")
fig = px.bar(df, x='Name', y=['Request Count', 'Failure Count'], 
             barmode='stack', 
             color_discrete_map={'Request Count': '#00FFAA', 'Failure Count': '#FF4B4B'})
fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

# 5. Stylized Heatmap Table (Wide view)
st.subheader("Detailed Performance Breakdown")
# Create a heatmap style for the latency column
styled_df = df.style.background_gradient(subset=['Average Response Time'], cmap='Reds')
st.dataframe(styled_df, use_container_width=True, hide_index=True)
# Create the CSV download button
csv = df.to_csv(index=False).encode('utf-8')

# 6. Glossary (Educational component for interview)
with st.expander("📚 Key Performance Concepts (Click to expand)"):
    st.write("""
    - **P99 Latency:** The response time that 99% of your requests are faster than. We use this to monitor 'tail latency' which directly affects user experience.
    - **Throughput (RPS):** The number of requests our system can handle per second before the sliding window counter begins rejecting traffic.
    - **Atomic Operations:** In our Redis/Lua implementation, this ensures that no two concurrent requests double-count a rate-limit increment, preventing race conditions.
    - **Fail-Open vs. Fail-Closed:** We configured the system to 'Fail-Open' during Redis outages to maintain service availability, at the cost of bypassing rate limits temporarily.
    """)
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
#     "pandas",
#     "platformdirs",
#     "python-dotenv",
#     "rich",
#     "seaborn",
#     "chardet",
#     "matplotlib",
# ]
# ///

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import httpx
import chardet

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjIwMDEyMjZAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.258FwOMudqFqmJOcpHoDjy5t7_fy8TqMM5L7uuSGo18"

def load_data(file_path):
    """
    Load CSV data with encoding detection.
    Detects the file encoding to handle diverse datasets.
    """
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    print(f"Detected file encoding: {encoding}")
    return pd.read_csv(file_path, encoding=encoding)

def analyze_data(df):
    """
    Perform advanced data analysis.
    Includes descriptive statistics, missing value checks, correlations, 
    and outlier detection for numeric columns.
    """
    numeric_df = df.select_dtypes(include=['number'])  # Select numeric columns
    analysis = {
        'summary': df.describe(include='all').to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'correlation': numeric_df.corr().to_dict(),
        'outliers': {
            col: numeric_df[col][(numeric_df[col] < numeric_df[col].quantile(0.05)) | 
                                 (numeric_df[col] > numeric_df[col].quantile(0.95))].tolist()
            for col in numeric_df.columns
        }
    }
    return analysis

def visualize_data(df):
    """
    Generate and save enhanced visualizations.
    Includes labeled histograms with dynamic colors and annotations for insights.
    """
    sns.set(style="whitegrid")
    numeric_columns = df.select_dtypes(include=['number']).columns
    for column in numeric_columns:
        plt.figure(figsize=(10, 6))
        sns.histplot(df[column].dropna(), kde=True, color="skyblue", edgecolor="black")
        plt.title(f'Distribution of {column}', fontsize=16)
        plt.xlabel(column, fontsize=14)
        plt.ylabel("Frequency", fontsize=14)
        mean_value = df[column].mean()
        plt.axvline(mean_value, color="red", linestyle="--", label=f"Mean: {mean_value:.2f}")
        plt.legend()
        plt.savefig(f'{column}_distribution.png')
        plt.close()

def generate_narrative(analysis):
    """
    Generate a detailed narrative using the LLM.
    Uses dynamic prompts to guide the LLM and include significant findings.
    """
    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }
    # Initial prompt for overall summary
    prompt = f"""
    Provide an analysis based on the following data:
    Summary: {analysis['summary']}
    Missing Values: {analysis['missing_values']}
    Correlations: {analysis['correlation']}
    Outliers: {analysis['outliers']}
    Highlight significant findings and their implications.
    """
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = httpx.post(API_URL, headers=headers, json=data, timeout=30.0)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error in narrative generation: {e}")
    return "Narrative generation failed."

def integrate_visualizations_in_narrative(narrative, numeric_columns):
    """
    Integrate generated visualizations into the Markdown narrative.
    """
    visuals = "\n".join([f"![{col} Distribution]({col}_distribution.png)" for col in numeric_columns])
    return narrative + "\n\n### Visualizations:\n" + visuals

def main(file_path):
    """
    Main workflow for loading data, analyzing, visualizing, and generating a narrative.
    Saves the narrative with visualizations to README.md.
    """
    print("Loading data...")
    df = load_data(file_path)
    
    print("Analyzing data...")
    analysis = analyze_data(df)
    
    print("Visualizing data...")
    visualize_data(df)
    
    print("Generating narrative...")
    narrative = generate_narrative(analysis)
    
    print("Integrating visualizations...")
    numeric_columns = df.select_dtypes(include=['number']).columns
    narrative_with_visuals = integrate_visualizations_in_narrative(narrative, numeric_columns)
    
    with open('README.md', 'w') as f:
        f.write(narrative_with_visuals)
    
    print("Analysis complete. Results saved to README.md.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)
    main(sys.argv[1])

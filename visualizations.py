import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def create_skill_progress_chart(skills):
    """
    Create a bar chart showing progress for each skill
    
    Args:
        skills: List of skill dictionaries with name and progress
        
    Returns:
        A Plotly figure object
    """
    if not skills:
        return go.Figure()
    
    # Create DataFrame from skills data
    df = pd.DataFrame([
        {"Skill": skill["name"], "Progress": skill["progress"]} 
        for skill in skills
    ])
    
    # Sort by progress for better visualization
    df = df.sort_values("Progress", ascending=False)
    
    # Create bar chart
    fig = px.bar(
        df,
        x="Skill",
        y="Progress",
        title="Skill Progress",
        labels={"Progress": "Progress (%)"},
        color="Progress",
        color_continuous_scale=["red", "yellow", "green"],
        range_color=[0, 100]
    )
    
    # Add line at 100% to indicate completion target
    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(df) - 0.5,
        y0=100,
        y1=100,
        line=dict(color="green", width=2, dash="dash")
    )
    
    # Customize layout for better appearance
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_range=[0, 105],
        height=400
    )
    
    return fig

def create_skills_radar_chart(skills):
    """
    Create a radar chart showing average progress by category
    
    Args:
        skills: List of skill dictionaries with category and progress
        
    Returns:
        A Plotly figure object
    """
    if not skills:
        return go.Figure()
    
    # Group skills by category and calculate average progress
    categories = {}
    for skill in skills:
        category = skill["category"]
        if category in categories:
            categories[category].append(skill["progress"])
        else:
            categories[category] = [skill["progress"]]
    
    # Calculate average progress for each category
    category_avg = {
        category: sum(progress) / len(progress)
        for category, progress in categories.items()
    }
    
    # Convert to lists for radar chart
    categories_list = list(category_avg.keys())
    progress_list = list(category_avg.values())
    
    # Add the first category at the end to close the loop
    categories_list.append(categories_list[0])
    progress_list.append(progress_list[0])
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=progress_list,
        theta=categories_list,
        fill='toself',
        name='Average Progress'
    ))
    
    # Customize layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        height=400
    )
    
    return fig

def create_progress_timeline(skills_history):
    """
    Create a line chart showing skill progress over time
    
    Args:
        skills_history: List of skill progress records with timestamps
        
    Returns:
        A Plotly figure object
    """
    if not skills_history:
        return go.Figure()
    
    # Create DataFrame from history data
    df = pd.DataFrame(skills_history)
    
    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Create line chart for each skill
    fig = px.line(
        df,
        x="timestamp",
        y="progress",
        color="skill_name",
        title="Progress Over Time",
        labels={
            "timestamp": "Date",
            "progress": "Progress (%)",
            "skill_name": "Skill"
        }
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Progress (%)",
        yaxis_range=[0, 100],
        height=400
    )
    
    return fig

def create_skill_heatmap(skills):
    """
    Create a heatmap showing skill progress by category and skill
    
    Args:
        skills: List of skill dictionaries with name, category, and progress
        
    Returns:
        A Plotly figure object
    """
    if not skills:
        return go.Figure()
    
    # Create DataFrame from skills data
    df = pd.DataFrame([
        {"Skill": skill["name"], "Category": skill["category"], "Progress": skill["progress"]} 
        for skill in skills
    ])
    
    # Pivot the data for heatmap
    pivot_df = df.pivot_table(
        values="Progress", 
        index="Category", 
        columns="Skill", 
        aggfunc="mean"
    ).fillna(0)
    
    # Create heatmap
    fig = px.imshow(
        pivot_df,
        labels=dict(x="Skill", y="Category", color="Progress (%)"),
        x=pivot_df.columns,
        y=pivot_df.index,
        color_continuous_scale=["red", "yellow", "green"],
        range_color=[0, 100]
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    
    return fig

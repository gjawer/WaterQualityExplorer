import streamlit as st
import pandas as pd
import dataretrieval.wqp as wqp
import plotly.express as px

st.title('Water Quality Explorer')

huc8 = st.text_input("Enter your HUC8 watershed of interest:", "########")
if len(huc8) != 8:
    st.error("HUC8 code must be 8 digits")

# Get projects within a HUC region
df, md = wqp.what_projects(huc=huc8)
df1 = df.loc[:,'ProjectIdentifier':'ProjectDescriptionText']

# Select project
project = st.selectbox("Pick a project:", df1.ProjectName.unique() )

# Select project ID
project_IDs = df1[df1.ProjectName == project]["ProjectIdentifier"].unique()
selected_ID = st.selectbox("Select project ID:", project_IDs)

# Print project description
st.write("Project Description:")
st.write(df1[df1.ProjectIdentifier == selected_ID]["ProjectDescriptionText"].values[0])

#Get PhsyChem results for project of choice
project_df, project_md =wqp.get_results(project=selected_ID, dataProfile= "resultPhysChem")

# Drop results that are "Not Reported"
data = project_df
data1 = data[data.ResultDetectionConditionText != "Not Reported"]

# Drop results that are Quality Control Sample-Field Blank or Quality Control Sample-Field Replicate
data2 = data1.loc[(data1.ActivityTypeCode != "Quality Control Sample-Field Blank"),:]
data2 = data2.loc[(data2.ActivityTypeCode != "Quality Control Sample-Field Replicate"),:]

# change non-detect numeric values to zeros and set units to be same as detection limit units
data3 = data2
data3.loc[data3.ResultDetectionConditionText == "Not Detected", "ResultMeasureValue"] = 0
data3.loc[data3.ResultDetectionConditionText == "Not Detected", "ResultMeasure/MeasureUnitCode"] = data3.loc[data3.ResultDetectionConditionText == "Not Detected", "DetectionQuantitationLimitMeasure/MeasureUnitCode"]

# Relevant columns only
data4 = data3.loc[:, ('MonitoringLocationName', 'ActivityStartDate',
                  'CharacteristicName', 'ResultMeasureValue',
                  'ResultMeasure/MeasureUnitCode', 'ActivityTypeCode')]

# Rename columns
data4.columns = ['site', 'date', 'param', 'result', 'unit', 'type']

# Ensure date column is in datetime format
data4.date = pd.to_datetime(data4.date)

# Ensure result column is in numeric format
data4.result = pd.to_numeric(data4.result, errors='coerce')

# Convert all ug/L into mg/L before reshaping-----------------------------------------------------
data5 = data4
data5.loc[data5.unit == "ug/L", "result"] = data5.loc[data5.unit == "ug/L", "result"] * 0.001

# Update row's unit to mg/L
data5.loc[data5.unit == "ug/L", "unit"]  = "mg/L"


# Plotting!
df = data5

# Boxplots
st.header("Boxplots")

# Select parameter
parameter = st.selectbox("Select parameter:", df.param.unique())

#Filter for selected parameter
param_df = df[df['param'] == parameter].sort_values(by='date')

#Create boxplots for specified parameter by site
box_fig = px.box(param_df, x="site", y="result", 
             title=parameter,
             color="site",
             points="all")
st.plotly_chart(box_fig)

#Create 
#Create time series for specified parameter by site
time_fig = px.line(param_df, x="date", y="result",
              color='site',
              title=parameter,
              markers=True)
st.plotly_chart(time_fig)
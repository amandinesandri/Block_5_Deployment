import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import copy
import boto3
import os


### Config
st.set_page_config(
    page_title="New Feature for delay",
    page_icon=" ",
    layout="wide"
)

# DATA_PATH = ('./src/get_around_delay_analysis.xlsx') # for a local loading

### App
st.title("Get Around's new feature study ")

### usual functions

@st.cache
# IMPORT DATA (CONNECTION WITH S3 BUCKET)
def import_data():

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("S3_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET")
    )

    response = s3_client.get_object(Bucket='get-around-app', Key="get_around_delay_analysis.csv")

    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")

    if status == 200:
        data = pd.read_csv(response.get("Body"))

    else:
        return f"Connection Error with S3... - Status code : {status}"


    #data = pd.read_excel(DATA_PATH)
    data = data.rename(columns={"checkin_type":"type",
                        "delay_at_checkout_in_minutes":"delay",
                        "previous_ended_rental_id":"prev_id",
                        "time_delta_with_previous_rental_in_minutes":"time_delta"})
    return data



st.markdown("""
    Here we perform some analysis to explore the impact of the new feature.
    The new feature 'Management of check-out delays' in the Get Arround application will not display the future location
    if it is too close to the previous location, because the previous user is late for checkout.
    Two parameters:
    - the scope: will this new feature be used for the mobile type of check-in? Or only for the connected type?
    - the threshold: how long for the minimum time between two rentals?
""")

st.markdown("""
    ------------------------
""")

st.header("Load and showcase data")

data_load_state = st.text('Loading data...')
data = import_data()
data_load_state.text("Data loaded") # change text from "Loading data..." to "" once the the load_data function has run

## Run the below code if the check is checked ✅
if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)


data_enable = data.loc[data['state']=='ended',:]

st.markdown("""
    ------------------------
""")

st.subheader("Repartition of the data by check_in type")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(""" All the rentals """)
    fig = px.pie(data,names='type')
    st.plotly_chart(fig, use_container_width=True)
    st.metric("Number of cases : ", len(data))

with col2:
    st.markdown(""" Effective (ended) rentals """)
    fig2 = px.pie(data.loc[data['state']=='ended',:],names='type')
    st.plotly_chart(fig2, use_container_width=True)
    st.metric("Number of cases : ", len(data.loc[data['state']=='ended',:]))

with col3:
    st.markdown(""" Canceled rentals """)
    fig3 = px.pie(data.loc[data['state']=='canceled',:],names='type')
    st.plotly_chart(fig3, use_container_width=True)
    st.metric("Number of cases : ", len(data.loc[data['state']=='canceled',:]))

st.markdown(""" COMMENT : Repartition of the check-in type seems to be
        very similar between the ended and canceled rentals""")

st.markdown("""
    ------------------------
""")

st.header("PROBLEMATIC : THE USER'S DELAY")

st.subheader("Distribution of the user's delay")

to_keep = abs(data_enable['delay'] - data_enable['delay'].mean()) <= 2*data_enable['delay'].std()
data_red = data_enable.loc[to_keep,:]

st.metric("Number of cases : ", len(data_red))
fig = px.histogram(data_red, 'delay', nbins=300, barmode='overlay', marginal='box')
st.plotly_chart(fig, use_container_width=True)


st.markdown("""
    This display was made without outliers, for a best view...
""")

st.markdown(""" COMMENT : Distribution of the user's delay is very symmetrical and tight""")

st.subheader("Users's delay by check-in type")

data_enable['late_or_early'] = data_enable['delay'].map(lambda v : 'late' if v > 0 else 'early')

data_enable.sort_values('late_or_early', inplace=True)

data_mobile = data_enable.loc[data['type']=='mobile',:]
data_connect = data_enable.loc[data['type']=='connect',:]

data_mobile.sort_values('late_or_early', inplace=True)
data_connect.sort_values('late_or_early', inplace=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(""" All the rentals""")
    st.metric("Number of cases : ", len(data_enable))
    fig = px.pie(data_enable,names='late_or_early')
    fig.update_traces(sort=False) 
    st.plotly_chart(fig, use_container_width=True)
    

with col2:
    st.markdown(""" Rentals with mobile check-in """)
    st.metric("Number of cases : ", len(data_mobile))
    fig2 = px.pie(data_mobile,names='late_or_early')
    fig2.update_traces(sort=False) 
    st.plotly_chart(fig2, use_container_width=True)
    

with col3:
    st.markdown(""" Rentals with connect check-in """)
    st.metric("Number of cases : ", len(data_connect))
    fig3 = px.pie(data_connect,names='late_or_early')
    fig3.update_traces(sort=False) 
    st.plotly_chart(fig3, use_container_width=True)
    
st.markdown(""" COMMENT : We can observe an increase of the user's delay for check-out
if the ckeck-in type is the mobile type. This type seems to be a little more problematic than the other.""")


st.subheader("Problematics cases")

st.markdown("""
    A problematic case is a case where the previous user's
    delay is higher than the time delta between the two rentals...

    We make this study just for the rentals with a PRESENT delta time value ... (delta_time <= 12 hours)
""")

data_join = data.merge(data[['rental_id', 'type', 'delay']], how='inner' , left_on='prev_id', right_on='rental_id' )
nb_time_delta_total = len(data_join)

data_join['problematic'] = data_join['time_delta'] < data_join['delay_y']
data_join['problematic'] = data_join['problematic'].apply(lambda v : 'problematic case' if v==True else 'non problematic case')

data_join_m = data_join.loc[data_join['type_x']=='mobile',:]
data_join_c = data_join.loc[data_join['type_x']=='connect',:]


col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(""" All the rentals""")
    st.metric("Number of cases : ", len(data_join))
    fig = px.pie(data_join,names='problematic')
    fig.update_traces(sort=False) 
    st.plotly_chart(fig, use_container_width=True)
    

with col2:
    st.markdown(""" Rentals with mobile check-in """)
    st.metric("Number of cases : ", len(data_join_m))
    fig2 = px.pie(data_join_m,names='problematic')
    fig2.update_traces(sort=False) 
    st.plotly_chart(fig2, use_container_width=True)
    

with col3:
    st.markdown(""" Rentals with connect check-in """)
    st.metric("Number of cases : ", len(data_join_c))
    fig3 = px.pie(data_join_c,names='problematic')
    fig3.update_traces(sort=False) 
    st.plotly_chart(fig3, use_container_width=True)

st.markdown(""" COMMENT : When we observe the problematic cases, we find again the same proportion.
Mobile check-in type seems to be a little more problematic than connect check-in type.""")


st.subheader("Problematic cases by threshold's choice value")

st.markdown("""
    Delta time is the time between the previous rental and the actual rental.
    Studying this delta time amounts to studying the effect of the threshold of the new feature...
    the choice of the threshold will directly impact which available locations will be displayed
    on the Get Arround application, depending on their delta time value.
    
    What is the number or proportion of problematic cases solved by a threshold choice?

    Note : We make this study just for the rentals with a PRESENT delta time value ... (delta_time <= 12 hours)
    """)

data_disp = copy.copy(data_join)

choice = st.selectbox("Select the global set or a subset by check-in type",['global data', 'connect type', 'mobile type'])
if choice == 'connect type':
    data_disp = data_join_c
elif choice == 'mobile type':
    data_disp = data_join_m


fig = px.histogram(data_disp, x='time_delta', nbins=100, color='problematic')
st.plotly_chart(fig, use_container_width=True)

st.markdown(""" COMMENT : For mobile check-in type, a threshold choice of 120 minutes could solve a very good proportion of the problematic cases.
For connect check-in type, perhaps we could take a smaller threshold : 60 or 90 minutes should be enough.""")

st.markdown("""
    ------------------------
""")

st.header("Impact of the threshold's choice")

st.markdown("""

    What proportion of effective and efficient rentals are affected by this threshold choice? (this is similar to looking at affected revenues for car owners)
""")


df_miss = pd.DataFrame(data_enable['time_delta'].unique(), columns=['threshold choice - (delta time value)'])
nb_total =len(data_enable)
df_miss['mobile type data'] = df_miss['threshold choice - (delta time value)'].apply(lambda thr : sum(data_mobile['time_delta'] < thr)*100 / nb_total)
df_miss['connect type data'] = df_miss['threshold choice - (delta time value)'].apply(lambda thr : sum(data_connect['time_delta'] < thr)*100 / nb_total)
df_miss['global data'] = df_miss['mobile type data'] + df_miss['connect type data']

set = st.selectbox("Select the global set or a subset by type of chek-in", ['global data','mobile type data', 'connect type data'])

fig = px.bar(df_miss, x='threshold choice - (delta time value)', y=set, barmode='group')
fig.update_yaxes(title='Affected rentals (%) of the effective and efficient rentals')
st.plotly_chart(fig, use_container_width=True)


st.markdown(""" COMMENT : If we apply the new feature with threshold around 60 / 90 / 120 minutes,
less than 2 percent of the effective rentals will be impacted.""")
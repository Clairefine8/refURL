import folium
import streamlit as st
import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
st.title("OCCU")
st.subheader("The all-in-one patient referral system for doctors.")

loc = st.sidebar.text_input('Enter patient address')
geolocator = Nominatim(user_agent="myApp")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
ptloc = geolocator.geocode(loc,timeout=10)
pt_coord = (ptloc.latitude, ptloc.longitude) 
specialtylist = pd.read_excel(io='/Users/claire/Desktop/work/Specialties.xlsx')
specialty= st.sidebar.selectbox('Specialty',options=specialtylist)

def display_gender_filter():
    return st.sidebar.radio('Female provider preferred?', ['Yes','N/A'])

def display_distance_filter():
    return st.sidebar.slider("Select maximum distance from patient (km)",min_value=0)

st.sidebar.write('Select wait times')
option_1 = st.sidebar.checkbox('0-1 week')
option_2 = st.sidebar.checkbox('1-2 weeks')
option_3 = st.sidebar.checkbox('2-4 weeks')
option_4 = st.sidebar.checkbox('4-8 weeks')
option_5 = st.sidebar.checkbox('8+ weeeks')

map = folium.Map(location=[43.706, -79.3670], tiles="OpenStreetMap")

def display_map (df,gender,address,radius,specialty,min,max):
    map = folium.Map(location=pt_coord, tiles="OpenStreetMap")

    from geopy.extra.rate_limiter import RateLimiter
    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="myApp")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    if specialty in set(df['Specialty']):
        df = df[(df['Specialty']==specialty)]
        df[['lat', 'lon']] = df['Location'].apply(
            geolocator.geocode,timeout=10).apply(lambda x: pd.Series(
                [x.latitude, x.longitude], index=['location_lat', 'location_long']))
        df['Distance'] = df.apply(lambda row: within_radius(row['lat'], row['lon'],pt_coord),axis=1)
        if gender =='Yes':
            df = df[(df['Gender']=='F')]
        df= df.loc[df['Distance'] <= radius]  
        df = df[(df['Wait time (weeks)']>=min)& (df['Wait time (weeks)']<=max)]
        for i in range (0,len(df)): 
            folium.Marker(
                location=[df.iloc[i]['lat'], df.iloc[i]['lon']],
                popup='Name: ' + df.iloc[i]['Name'] + "\n Specialty: " + df.iloc[i]['Specialty']+ "\n Wait time (weeks): " + str(df.iloc[i]['Wait time (weeks)']),icon_color='green').add_to(map)
    else: df = df 
    return map


#load data
data=pd.read_excel(io='/Users/claire/Desktop/work/doctors.xlsx')
 #display filters and map
wait = []
if option_1 ==1: 
    wait = [0,1]
if option_2 == 1:
    wait = wait + [1,2]
if option_3 == 1:
    wait = [2,4]
if option_4 == 1:
    wait = [4,8]
if option_5 ==1:
    wait = [8,1000]

unique_wait = set(wait)
min_wait = min(unique_wait)
max_wait = max(unique_wait)

gender = display_gender_filter()
distance = display_distance_filter()
import math
from geopy.distance import geodesic as GD
def within_radius (lat,long,y):
        x = (lat,long)
        return GD(x,y).km 

note=st.sidebar.text_area("Paste visit note")
map = display_map(data,gender,pt_coord,distance, specialty,min_wait,max_wait)

map



import openai
openai.api_key = st.text_input("Enter API key for open AI if you would like to create an automated referral")

def chat_with_chatgpt(prompt, specialty, model="text-davinci-003"):
    response = openai.Completion.create(
        engine=model,
        prompt = "Write a doctor's referral to the specialty of" + specialty + 
        "based off the following information: " + prompt + ". Do this in a concise format that starts with Dear Dr. and a line indent",
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )
    message = response.choices[0].text.strip()
    return message

if len(openai.api_key)>1: 
    st.text_area(label="Referral",value=chat_with_chatgpt(note,specialty),height=400)




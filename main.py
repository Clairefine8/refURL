import folium
import streamlit as st
import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
import requests 
from io import BytesIO
st.title("OCCU")
st.subheader("The all-in-one patient referral system for doctors.")
st.text("Please fill out the side bar to search for doctors")
loc = st.sidebar.text_input('Enter patient address - must be in Toronto or the Greater Toronto Area')
geolocator = Nominatim(user_agent="myApp")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
url_specialties = "https://github.com/Clairefine8/refURL/raw/main/Specialties.xlsx"
my_specialties = requests.get(url_specialties).content
specialtylist = pd.read_excel(my_specialties)
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


def display_map (df,gender,address,radius,specialty,min,max):
    # for now we will default the map to zoom to Toronto
    # when we have more cities, change the code to: 
         # map = folium.Map(location=pt_coord, tiles="OpenStreetMap")
    map = folium.Map(location=(43.706, -79.367), tiles="OpenStreetMap")
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



 #display filters and map
wait = []
if option_1 ==1: 
    wait = [0,1]
if option_2 == 1:
    wait = wait + [1,2]
if option_3 == 1:
    wait = wait + [2,4]
if option_4 == 1:
    wait = wait +  [4,8]
if option_5 ==1:
    wait =  wait + [8,1000]

unique_wait = set(wait)
if wait:
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
#load data
url_doctors = "https://github.com/Clairefine8/refURL/raw/main/doctors.xlsx"
my_doctors = requests.get(url_doctors).content
data = pd.read_excel(my_doctors)
if (type(loc) == str) & (bool(wait)==True) & (type(specialty)==str):  
    ptloc = geolocator.geocode(loc,timeout=10)
    pt_coord = (ptloc.latitude, ptloc.longitude)  
    map = display_map(data,gender,pt_coord,distance, specialty,min_wait,max_wait)
    map



import openai
openai.api_key = st.text_input("Enter your unique open AI API key if you would like to create an automated referral from your visit note")

def chat_with_chatgpt(prompt, specialty, model="text-davinci-003"):
    response = openai.Completion.create(
        engine=model,
        prompt = "Write a doctor's referral to the specialty of" + specialty + 
        "based off the following information: " + prompt + ". Do this in a concise format that starts with Dear Dr. and a line indent",
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.5,
    )
    message = response.choices[0].text.strip()
    return message

if len(openai.api_key)>1: 
    st.text_area(label="Referral",value=chat_with_chatgpt(note,specialty),height=400)




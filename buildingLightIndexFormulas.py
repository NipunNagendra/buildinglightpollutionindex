from math import radians, sin, cos, sqrt, atan2, pi
import folium
import numpy as np
import pandas as pd


def haversineDistance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


def filterOutliers(data, threshold_meters):
    latitudes = data['Latitude']
    longitudes = data['Longitude']

    reference_lat = latitudes.mean()
    reference_lon = longitudes.mean()

    distances = [haversineDistance(reference_lat, reference_lon, lat, lon) for lat, lon in zip(latitudes, longitudes)]

    data['Distance'] = distances

    filtered_data = data[data['Distance'] <= (threshold_meters / 1000)].reset_index(drop=True)

    filtered_data = filtered_data.drop('Distance', axis=1)

    return filtered_data



def trustValue(data, num_nearest=1):
    data_copy = data.copy()
    data_copy['TrustValue'] = 0

    for i in range(len(data_copy)):
        lat, lon = data_copy['Latitude'][i], data_copy['Longitude'][i]

        distances = data_copy.apply(lambda row: haversineDistance(lat, lon, row['Latitude'], row['Longitude']), axis=1)
        nearest_indices = distances.nsmallest(num_nearest + 1).index[1:]

        nearest_data = data_copy.loc[nearest_indices].copy()
        avg = nearest_data['MagReading'].mean()
        data_copy['TrustValue'][i] = 1-((abs(data_copy['MagReading'][i] - avg)) / avg)

    return data_copy


def drawCircles(data):
    data = trustValue(data)
    data = data.sort_values(by=['TrustValue'], ascending=False)
    data = data.reset_index(drop=True)
    data['trustedRadius'] = 0
    map = folium.Map(location=[30.467883, -97.838090], zoom_start=100, max_zoom=10000, tiles="cartodb positron")

    centerLat = (data['Latitude'].max() + data['Latitude'].min()) / 2
    centerLon = (data['Longitude'].max() + data['Longitude'].min()) / 2
    radiusToEdge = haversineDistance(centerLat, centerLon, data['Latitude'].max(), data['Longitude'].max())
    #folium.Circle(location=[centerLat, centerLon], radius=radiusToEdge * 1000, color='blue', fill=True).add_to(map)

    for i in range(len(data)):
        lat = data['Latitude'][i]
        lon = data['Longitude'][i]
        trust = data['TrustValue'][i]
        #folium.Circle(location=[lat, lon], radius=trust * radiusToEdge/2 * 1000, color='red', fill=True).add_to(map)
        data['trustedRadius'][i] = trust * (radiusToEdge/2) * 1000

    for i in range(len(data)):
        lat = data['Latitude'][i]
        lon = data['Longitude'][i]
        folium.Marker([lat, lon], popup=str((data['MagReading'][i]))+":MagReading and TrustValue:"+str(data['TrustValue'][i])).add_to(map)

    return data, radiusToEdge * 1000, map, centerLon, centerLat


def magsAToCandelaM(magReading):
    return 10.8 * (10**4) * (10**(-0.4 * magReading))


def aggregateSumCandela(data):
    data['Candela'] = 0
    for i in range(len(data)):
        data['Candela'][i] = magsAToCandelaM(data['MagReading'][i]) * pi * (data['trustedRadius'][i]**2)
    return data, data['Candela'].sum()

def wholeSumCandela(data, edgeRadius):
    return 10.8 * (10**4) * (10**(-0.4 * data['MagReading'].sum()))*pi*(edgeRadius**2)


def plotPointsFolium(data):
    map.show_in_browser()

def normalizeIndex(index):
    minIndex=-8
    maxIndex=15
    return abs(round(((index-minIndex)/(maxIndex-minIndex))*10,2))
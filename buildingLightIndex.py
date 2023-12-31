import math

import folium
import pandas as pd
import buildingLightIndexFormulas as blif


def processCSV(path):
    try:
        df = pd.read_csv(path, header=None,
                         names=["Latitude", "Longitude", "ReadingStatus", "MagReading", "FrequencyHz",
                                "PeriodCounts", "PeriodSeconds", "TemperatureC", "Timestamp"])
    except pd.errors.ParserError as e:
        print(f"Error reading CSV file: {e}")
        return None
    df['Timestamp'] = df.index
    df = df.reset_index(drop=True)
    df = df.dropna()

    df['MagReading'] = df['MagReading'].astype(str).str.rstrip('m').astype(float)
    df['Latitude'] = df['Latitude'].astype(float)
    df['Longitude'] = df['Longitude'].astype(float)

    df['MagReading']=df['MagReading']-8

    return df


if __name__ == "__main__":
    df = processCSV("test.csv")

    #df = blif.filterOutliers(df, 3)
    df, edgeRadius, map, centerLon, centerLat = blif.drawCircles(df)
    df, aggregateCandelaSum = blif.aggregateSumCandela(df)

    index=2.5 * math.log10(abs(aggregateCandelaSum))
    normalizedIndex = blif.normalizeIndex(index)
    folium.Circle(location=[centerLat, centerLon], radius=edgeRadius, color='blue', fill=True, popup=str(normalizedIndex)).add_to(map)

    map.show_in_browser()
    print(f"normalized index: {blif.normalizeIndex(index)}")
    print(f"Aggregate Candela Sum: {aggregateCandelaSum}")
    print(df.to_string())

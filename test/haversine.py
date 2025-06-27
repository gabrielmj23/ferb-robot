import math

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 * 1000 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r


# print(haversine(8.2959462, -62.7119729, 8.295995, -62.712056))  # Should be 0
print(haversine(8.295925, -62.711975, 8.295995, -62.712056))  # Should be 0
import json

# Utilities to attach data from matched Parcel objects to ZooniverseSubject and ManualCovenant

def get_parcel_addresses(obj):
    return list(obj.parcel_matches.all().values('street_address', 'city', 'state', 'zip_code'))

def get_parcel_cities(obj):
    return obj.parcel_matches.all().values_list('city', flat=True)

def set_addresses(obj):
    if obj.bool_parcel_match:
        obj.parcel_addresses = json.dumps(get_parcel_addresses(obj))
        cities = get_parcel_cities(obj)
        if len(cities) > 0:
            # Assuming for the most part that we can generally take the first city we find. There will be edge cases, but those can be accessed via the address JSON object and this one is more of a shorthand
            obj.parcel_city = cities[0]
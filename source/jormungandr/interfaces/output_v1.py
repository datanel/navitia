# coding=utf8
from conf import base_url
from instance_manager import NavitiaManager, DeadSocketException, RegionNotFound
from renderers import render
import request_pb2, type_pb2#, response_pb2
from uri import collections_to_resource_type, resource_type_to_collection
from error import generate_error
from sets import Set

class json_renderer:
    nearbyable_types = ['stop_points', 'stop_areas', 'coords', 'pois']
    pbtype_2_collection = {type_pb2.STOP_AREA : "stop_areas",
                           type_pb2.STOP_POINT : "stop_points"}

    def __init__(self, base_url):
        self.base_url = base_url
        self.visited_types = Set()

    def stop_point(self, obj, region, details=False, name_and_uri=True):
        return self.generic_type('stop_points', obj, region, details, name_and_uri)

    def stop_area(self, obj, region, details=False, name_and_uri=True):
        return self.generic_type('stop_areas', obj, region, details, name_and_uri)

    def route(self, obj, region, details=False):
        result = self.generic_type('routes', obj, region, details)
        try:
            if obj.HasField("is_frequence"):
                result["is_frequence"] = obj.is_frequence
        except:
            pass
        try:
            if obj.HasField("line"):
                result["line"] = self.line(obj.line, region, details)
        except:
            pass
        return result

    def line(self, obj, region, details=False):
        return self.generic_type('lines', obj, region, details)

    def network(self, obj, region, details=False):
        result = self.generic_type('networks', obj, region, details)
        try:
            result["lines"] = []
            for line in obj.lines:
                result["lines"].append(self.line(line, region, details))
        except:
            del result['lines']
        return result

    def commercial_mode(self, obj, region, details=False):
        result = self.generic_type('commercial_modes', obj, region, details)
        try:
            result["physical_modes"] = []
            for physical_mode in obj.physical_modes:
                result["physical_modes"].append(self.physical_mode(physical_mode, region, details))
        except:
            del result['physical_modes']
        return result


    def physical_mode(self, obj, region, details=False):
        result = self.generic_type('physical_modes', obj, region, details)
        try:
            result["commercial_modes"] = []
            for commercial_mode in obj.commercial_modes:
                result["commercial_modes"].append(self.commercial_mode(commercial_mode, region, details))
        except:
            del result['commercial_modes']
        return result

    def poi_type(self, obj, region, details=False):
        return self.generic_type("poi_types", obj, region, details)

    def poi(self, obj, region, details):
        result = self.generic_type('pois', obj, region, details)
        if obj.HasField("poi_type"):
            result["poi_type"] = self.poi_type('poi_types', obj.poi_type, region, details)
        return result



    def company(self, obj, region, details=False):
        return self.generic_type('companies', obj, region, details)

    def address(self, obj, region, details=False, name_and_uri=False):
        result = self.generic_type('addresses', obj, region, details, name_and_uri)
        if obj.HasField("house_number"):
            result["house_number"] = obj.house_number
        return result

    def administrative_region(self, obj, region, details):
        self.visited_types.add("administrative_regions")
        result = self.generic_type('administrative_regions', obj, region, details)
        try:
            if obj.HasField("zip_code"):
                result["zip_code"] = obj.zip_code
        except:
            pass
        try:
            if obj.HasField("level"):
                result["level"] = obj.level
        except:
            pass
        return result

    def stop_time(self, obj, region = None, details = False):
        return obj

    def route_schedule(self, obj, uri) : 
        result = {'table' : {"rows" : []}, 'route' : {} }
        
        for row in obj.table.rows : 
            r = {}
            if row.stop_point:
                r['stop_point'] = self.stop_point(row.stop_point, uri.region())
            if row.stop_times:
                for stop_time in row.stop_times: 
                    if not 'stop_times' in r:
                        r['stop_times'] = []
                    r['stop_times'].append(self.stop_time(stop_time))
            result['table']['rows'].append(r)

        return result

    def journey(self, obj, uri, details, is_isochrone, arguments):
        result = {
                'duration': obj.duration,
                'nb_transfers': obj.nb_transfers,
                'departure_date_time': obj.departure_date_time,
                'arrival_date_time': obj.arrival_date_time,
                }
        if obj.HasField('origin'):
            self.visited_types.add("origin")
            result['origin'] = self.place(obj.origin, uri.region())
        if obj.HasField('destination'):
            self.visited_types.add("destination")
            result['destination'] = self.place(obj.destination, uri.region())

        if len(obj.sections) > 0:
            result['sections'] = []
            for section in obj.sections:
                result['sections'].append(self.section(section, uri.region()))

        if is_isochrone:
            params = "?"
            if obj.HasField('origin'):
                params = params + "from=" + obj.origin.uri + "&"
            else:
                params = params + "from=" + uri.uri + "&"
            if obj.HasField('destination'):
                resource_type = json_renderer.pbtype_2_collection[obj.destination.embedded_type]
                params = params + "to=" + uri.region() + "/" +resource_type +"/" + obj.destination.uri

            ignored_params = ["origin", "destination"]
            for k, v in arguments.givenByUser().iteritems():
                if not k in ignored_params:
                    params = params + "&" + k + "=" + v

            result["href"] = base_url + "/v1/journeys"+params
        return result

    def departures(self, obj):
        pass
        #result = {}

    def place(self, obj, region_name):
        obj_t = None
        result = {"name" :"", "id":"", "embedded_type" : ""}
        if obj.embedded_type == type_pb2.STOP_AREA:
            obj_t = obj.stop_area
            result["embedded_type"] = "stop_area"
            result["stop_area"] = self.stop_area(obj.stop_area, region_name, False, False)
        elif obj.embedded_type == type_pb2.STOP_POINT:
            obj_t = obj.stop_point
            result["embedded_type"] = "stop_point"
            result["stop_point"] = self.stop_point(obj.stop_point, region_name, False, False)
        elif obj.embedded_type  == type_pb2.ADDRESS:
            obj_t = obj.address
            result["embedded_type"] = "address"
            result["address"] = self.address(obj.address, region_name, False, False)
        if obj_t:
            #self.visited_types.add(result["embedded_type"])
            result["name"] = obj_t.name
            result["id"] = region_name + "/" + resource_type_to_collection[result["embedded_type"]]+"/"+obj.uri
        return result

    def region(self, obj, region_id, details=False):
        result = {
                'id': region_id,
                'start_production_date': obj.start_production_date,
                'end_production_date': obj.end_production_date,
                'status': 'running',
                'shape': obj.shape
                }
        return result


    def generic_type(self, type, obj, region, details = False, name_and_uri=True):
        result = {}
        if name_and_uri : 
            result['name'] = obj.name
            result['id'] = region + '/' + type + '/' + obj.uri
        try: # si jamais y’a pas de champs coord dans le .proto, HasField gère une exception
            if obj.HasField('coord'):
                result['coord'] = {'lon': obj.coord.lon, 'lat': obj.coord.lat}
        except:
            pass
        try:
            result['administrative_regions'] = []
            for admin in obj.administrative_regions:
                result['administrative_regions'].append(self.administrative_region(admin, region, False))
        except:
            pass
        if len(result['administrative_regions'])==0:
            del result['administrative_regions']
        return result

    def section_links(self, region_name, uris):
        links = []
        if uris.HasField('company'):
            links.append({"href" : self.base_url + region_name + '/companies/' + uris.company,
                      "templated" : False,
                      "rel" : "company"})
        if uris.HasField('vehicle_journey'):
            links.append({"href" : self.base_url + region_name + '/vehicle_journeys/' + uris.vehicle_journey,
                       "templated" : False,
                       "rel" : "vehicle_journey"})
        if uris.HasField('line'):
            links.append({"href" : self.base_url + region_name + '/lines/' + uris.line,
                       "templated" : False,
                       "rel" : "line"})
        if uris.HasField('route'):
            links.append({"href" : self.base_url + region_name + '/routes/' + uris.route,
                       "templated" : False,
                       "rel" : "route"})
        if uris.HasField('commercial_mode'):
            links.append({"href" : self.base_url + region_name + '/commercial_modes/' + uris.commercial_mode,
                       "templated" : False,
                       "rel" : "commercial_mode"})
        if uris.HasField('physical_mode'):
            links.append({"href" : self.base_url + region_name + '/physical_modes/' + uris.physical_mode,
                       "templated" : False,
                       "rel" : "physical_mode"})
        if uris.HasField('network'):
            links.append({"href" : self.base_url + region_name + '/networks/' + uris.network,
                       "templated" : False,
                       "rel" : "network"})
        return links

    def display_informations(self, infos):
        result = {
                'network': infos.network,
                'code': infos.code,
                'headsign': infos.headsign,
                'color': infos.color,
                'commercial_mode': infos.commercial_mode,
                'physical_mode': infos.physical_mode
                }
        return result

    def street_network(self, street_network):
        result = {
                'length': street_network.length,
                'mode': street_network.mode,
                'instructions': [],
                'coordinates': []
                }
        for item in street_network.path_items:
            result['instructions'].append({'name': item.name, 'length': item.length})

        for coord in street_network.coordinates:
            result['coordinates'].append({'lon': coord.lon, 'lat': coord.lat})

        return result

    def stop_date_time(self, obj, region_name):
        result = {}
        if obj.HasField('departure_date_time'):
            result['departure_date_time'] = obj.departure_date_time
        if obj.HasField('arrival_date_time'):
            result['arrival_date_time'] = obj.arrival_date_time
        if obj.HasField('stop_point'):
            self.visited_types.add("stop_point")
            result['stop_point'] = self.stop_point(obj.stop_point, region_name)
        return result


    def section(self, obj, region_name):
        self.visited_types.add("origin")
        self.visited_types.add("destination")
        result = {
                'type': obj.type,
                'origin': self.place(obj.origin, region_name),
                'destination': self.place(obj.destination, region_name),
                'duration': obj.duration
                }
        if obj.HasField('begin_date_time'):
            result['begin_date_time'] = obj.begin_date_time
        if obj.HasField('end_date_time'):
            result['end_date_time'] = obj.end_date_time
        if obj.HasField('uris'):
            result['links'] = self.section_links(region_name, obj.uris)
        if obj.HasField('pt_display_informations'):
            result['pt_display_informations'] = self.display_informations(obj.pt_display_informations)

        if len(obj.stop_date_times) > 0:
            result['stop_date_times'] = []
            for stop_dt in obj.stop_date_times:
                result['stop_date_times'].append(self.stop_date_time(stop_dt, region_name))

        if obj.HasField('street_network'):
            result['street_network'] = self.street_network(obj.street_network)

        if obj.HasField('transfer_type'):
            result['transfert_type'] = obj.transfer_type

        return result

    def passage(self, obj, region_name):
        result = {
                'stop_date_time': self.stop_date_time(obj.stop_date_time, region_name),
                'stop_point': self.stop_point(obj.stop_point, region_name),
                }
        try:
            result['route'] = self.route(obj.vehicle_journey.route, region_name)
        except:
            del result['route']
            pass
        try:
            if obj.HasField('pt_display_informations'):
                result['pt_display_informations'] = self.display_informations(obj.pt_display_informations)
        except:
            pass
        return result

    def link_types(self, region_name):
        t_url = base_url + "/v1/coverage/{"
        result = []
        for t in self.visited_types:
            result.append({"href":t_url+t+".id}", "rel": t, "templated":"true"})
        return result




def get_field_by_name(obj, name):
    for field_tuple in obj.ListFields():
        if field_tuple[0].name == name:
            return field_tuple[1] 
    return None

def pagination(base_url, obj):
    result = {}
    result['total_result'] = obj.totalResult
    result['current_page'] = obj.startPage
    result['items_on_page'] = obj.itemsOnPage
    return result

def pagination_links(base_url, obj):
    result = []
    result.append({'href' : base_url, 'rel' : 'first', "templated":False})
    if obj.itemsOnPage > 0:
        result.append({'href' : base_url + '?start_page=' +
                       str(int(obj.totalResult/obj.itemsOnPage)), "rel" : "last", "templated":False})
    else:
        result.append({'href' : base_url, "rel" : "last", "templated":False})
    if obj.HasField('nextPage'):
        result.append({'href' : base_url + '?start_page=' + str(obj.startPage + 1), "rel" : "next", "templated":False})
    if obj.HasField('previousPage'):
        result.append({'href' : base_url + '?start_page=' + str(obj.startPage - 1), "rel" : "prev", "templated":False})
    return result


def render_ptref(response, region, resource_type, uid, format, callback):
    if response.error and response.error == '404':
        return generate_error("No object found", status=404)
    
    resp_dict = dict([(resource_type, []), ("links", []), ("pagination", {})])
    resp_dict[resource_type] = []
    renderer = json_renderer(base_url + '/v1/coverage')
    renderer.visited_types.add(resource_type)
    items = get_field_by_name(response, resource_type)
    if items:
        for item in items:
            resp_dict[resource_type].append(renderer.generic_type(resource_type, item, region))
    resp_dict['pagination'] = pagination(base_url + '/v1/coverage/' + region + '/' + resource_type, response.pagination)

    if not uid:
        resp_dict['links'] = pagination_links(base_url+ '/v1/coverage/' + region + '/' + resource_type , response.pagination)
    
    if uid:
        link_first_part = base_url+"/v1/coverage/"+ region+"/"+resource_type+"/"+uid
        if resource_type in json_renderer.nearbyable_types:
            resp_dict['links'].append({"href" : link_first_part+"/journeys", "rel":"journeys", "templated":False})
            resp_dict['links'].append({"href" : link_first_part+"/places_nearby", "rel":"places_nearby", "templated":False})
            #resp_dict['curies'].append({"href" : base_url+"/v1/coverage/{"+resource_type+".id/route_schedules", "rel":"route_schedules"})
            #resp_dict['curies'].append({"href" : base_url+"/v1/coverage/{"+resource_type+".id/stop_schedules", "rel":"stop_schedules"})
            resp_dict['links'].append({"href" : link_first_part+"/departures", "rel":"departures", "templated":False})
            resp_dict['links'].append({"href" : link_first_part+"/arrivals", "rel":"arrivals", "templated":False})
        for key in collections_to_resource_type:
            if key != type:
                resp_dict['links'].append({"href" : link_first_part+"/"+key, "rel":""+key, "templated":False}) 
    else:
        resp_dict['links'].append({"href" : base_url + "/v1/coverage/{"+resource_type+".id}", "rel" : "related", "templated":True})

    resp_dict['links'].extend(renderer.link_types(region))
    return render(resp_dict, format, callback)

def coverage(request, region_name=None, format=None):
    region_template = "{regions.id}"
    if region_name:
        region_template = region_name
    result = {'regions': [], 
              'links' : []}

    links =  [{"href" : base_url +"/v1/coverage/"+region_template, "rel":"related"}]

    for key in collections_to_resource_type:
        links.append({"href" : base_url+"/v1/coverage/"+region_template+"/"+key, "rel":""+key})

    result['links'] = links

    for link in result['links']:
        link["templated"] = region_name==None
    
    if not region_name:
        regions = NavitiaManager().instances.keys() 
    else:
        regions = {region_name}
    
    renderer = json_renderer(base_url + '/v1/')
    req = request_pb2.Request()
    req.requested_api = type_pb2.METADATAS
    for r_name in regions:
        try:
            resp = NavitiaManager().send_and_receive(req, r_name) 
            result['regions'].append(renderer.region(resp.metadatas, r_name))
        except DeadSocketException :
            if region_name:
                return generate_error('region : ' + r_name + ' is dead', 500)
            else :
                result['regions'].append({"id" : r_name, "status" : "not running", "href": base_url + "/v1/" + r_name})
        except RegionNotFound:
            if region_name:
                return generate_error('region : ' + r_name + " not found ", 404)
            else: 
                result['regions'].append({"id" : r_name, "status" : "not found", "href": base_url + "/v1/" + r_name})
    
    return render(result, format,  request.args.get('callback'))

def coord(request, lon_, lat_):
    try:
        lon = float(lon_)
        lat = float(lat_)
    except ValueError:
        return generate_error("Invalid coordinate : " +lon_+":"+lat_, 400)

    result_dict = {"coord" : {"lon":lon, "lat": lat, "regions" : []}, "links":[]}
    
    region_key = NavitiaManager().key_of_coord(lon, lat)
    if(region_key):
        result_dict["coord"]["regions"].append({"id":region_key})

    result_dict["links"].append({"href":base_url + "/v1/coverage/coord/"+lon_+";"+lat_+"/journeys", "rel" :"journeys", "templated":False})
    result_dict["links"].append({"href":base_url + "/v1/coverage/coord/"+lon_+";"+lat_+"/places_nearby", "rel" :"nearby", "templated":False})
    result_dict["links"].append({"href":base_url + "/v1/coverage/coord/"+lon_+";"+lat_+"/departures", "rel" :"departures", "templated":False})
    result_dict["links"].append({"href":base_url + "/v1/coverage/coord/"+lon_+";"+lat_+"/arrivals", "rel" :"arrivals", "templated":False})
    result_dict["links"].append({"href":"www.openstreetmap.org/?mlon="+lon_+"&mlat="+lat_+"&zoom=11&layers=M", "rel":"about", "templated":False})

    return render(result_dict, "json", request.args.get('callback'))


def index(request, format='json'):
    response = {
            "links" : [
                    {"href" : base_url + "/v1/coverage", "rel" :"coverage", "title" : "Coverage of navitia"},
                    {"href" : base_url + "/v1/coord", "rel" : "coord", "title" : "Inverted geocooding" },
                    {"href" : base_url + "/v1/journeys", "rel" : "journeys", "title" : "Compute journeys"}
                    ]  
            }
    return render(response, format, request.args.get('callback'))

def reconstruct_pagination_journeys(string, region_name):
    args = []

    for arg_and_val in string.split("&"):
        if len(arg_and_val.split("=")) == 2:
            arg, val = arg_and_val.split("=")
            if arg == "origin" or arg == "destination":
                resource_type, uid = val.split(":")
                val = region_name + "/" + resource_type_to_collection[resource_type] + "/" + val
                if arg == "origin":
                    arg = "from"
                else:
                    arg = "to"
            args.append(arg+"="+val)
    return "&".join(args)

def journeys(arguments, uri, response, format, callback, is_isochrone=False):
    renderer = json_renderer(base_url + '/v1/')
    response_dict = {'journeys': [], "links" : []}
    for journey in response.journeys:
        response_dict['journeys'].append(renderer.journey(journey, uri, True, is_isochrone, arguments))
    response_dict['links'].extend(renderer.link_types(uri.region()))
    if not is_isochrone:
        prev = reconstruct_pagination_journeys(response.prev, uri.region())
        next = reconstruct_pagination_journeys(response.next, uri.region())
        response_dict['links'].append({"href":base_url+"/v1/journeys?"+next, "rel":"next","templated":False })
        response_dict['links'].append({"href":base_url+"/v1/journeys?"+prev, "rel":"prev","templated":False })
    return render(response_dict, format, callback)

def departures(response, region, format, callback):
    renderer = json_renderer(base_url + '/v1/')
    renderer.visited_types.add('departures')
    response_dict = {'departures': [], "links" : [], "pagination" : {}}
    response_dict['pagination']['total_result'] = len(response.places)
    response_dict['pagination']['current_page'] = 0
    response_dict['pagination']['items_on_page'] = len(response.places) 

    for passage in response.next_departures:
        response_dict['departures'].append(renderer.passage(passage, region))
    response_dict['links'] = renderer.link_types(region)
    return render(response_dict, format, callback)

def arrivals(response, region, format, callback):
    renderer = json_renderer(base_url + '/v1/')
    renderer.visited_types.add('arrivals')
    response_dict = {'arrivals': [], "pagination": {}, "links" : []}
    response_dict['pagination']['total_result'] = len(response.next_arrivals)
    response_dict['pagination']['current_page'] = 0
    response_dict['pagination']['items_on_page'] = len(response.next_arrivals) 
    for passage in response.next_arrivals:
        response_dict['arrivals'].append(renderer.passage(passage, region))
    response_dict['links'] = renderer.link_types(region)
    return render(response_dict, format, callback)

def places(response, uri, format, callback):
    renderer = json_renderer(base_url + '/v1/')
    renderer.visited_types.add("places")
    response_dict = {"links" : [], "pagination" : {}, "places" : []}

    response_dict['pagination']['total_result'] = len(response.next_departures)
    response_dict['pagination']['current_page'] = 0
    response_dict['pagination']['items_on_page'] = len(response.next_departures) 
    for place in response.places:
        response_dict['places'].append(renderer.place(place, uri.region()))
        response_dict['places'][-1]['quality'] = place.quality
    
    response_dict['links'].append({"href" : base_url+"/v1/coverage/{places.id}",
                                   "rel" : "places.id",
                                   "templated" : True})
    
    return render(response_dict, format, callback)
    

def nearby(response, uri, format, callback):
    renderer = json_renderer(base_url + '/v1/')
    renderer.visited_types.add("places_nearby")
    response_dict = {"links" : [], "pagination" : {}, "places_nearby" : []}
    response_dict['pagination']['total_result'] = len(response.places_nearby)
    response_dict['pagination']['current_page'] = 0
    response_dict['pagination']['items_on_page'] = len(response.places_nearby) 
    for place in response.places_nearby:
        response_dict['places_nearby'].append(renderer.place(place, uri.region()))
        response_dict['places_nearby'][-1]['distance'] = place.distance
    
    response_dict['links'] = renderer.link_types(uri.region())
    return render(response_dict, format, callback)

def route_schedules(response, uri, format, callback):
    renderer = json_renderer(base_url+'/v1/')
    response_dict = {"links" : [], "route_schedules" : []}

    for schedule in response.route_schedules:
        response_dict['route_schedules'].append(renderer.route_schedule(schedule, uri))

    return render(response_dict, format, callback)
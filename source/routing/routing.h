/* Copyright © 2001-2014, Canal TP and/or its affiliates. All rights reserved.
  
This file is part of Navitia,
    the software to build cool stuff with public transport.
 
Hope you'll enjoy and contribute to this project,
    powered by Canal TP (www.canaltp.fr).
Help us simplify mobility and open public transport:
    a non ending quest to the responsive locomotion way of traveling!
  
LICENCE: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
   
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.
   
You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
  
Stay tuned using
twitter @navitia 
IRC #navitia on freenode
https://groups.google.com/d/forum/navitia
www.navitia.io
*/

#pragma once

#include "type/pt_data.h"
#include "type/datetime.h"

namespace navitia { namespace routing {
    using type::idx_t;

struct NotFound{};




/** Représente un horaire associé à un validity pattern
 *
 * Il s'agit donc des horaires théoriques
 */
struct ValidityPatternTime {
    idx_t vp_idx;
    int hour;

    template<class T>
    bool operator<(T other) const {
        return hour < other.hour;
    }

    ValidityPatternTime() : vp_idx(type::invalid_idx), hour(-1) {}
    ValidityPatternTime(idx_t vp_idx, int hour) : vp_idx(vp_idx), hour(hour){}
};


enum class ItemType {
    public_transport,
    walking,
    stay_in,
    waiting
};

inline std::ostream& operator<< (std::ostream& ss, ItemType t) {
    switch (t) {
    case ItemType::public_transport: return ss << "public_transport";
    case ItemType::walking: return ss << "transfer";
    case ItemType::stay_in: return ss << "stay_in";
    case ItemType::waiting: return ss << "waiting";
    }
    return ss;
}

/** Étape d'un itinéraire*/
struct PathItem {
    boost::posix_time::ptime arrival = boost::posix_time::pos_infin;
    boost::posix_time::ptime departure = boost::posix_time::pos_infin;
    std::vector<boost::posix_time::ptime> arrivals;
    std::vector<boost::posix_time::ptime> departures;
    std::vector<const nt::StopTime*> stop_times; //empty if not public transport

    /**
     * if public transport, contains the list of visited stop_point
     * for transfers, contains the departure and arrival stop points
     */
    std::vector<const navitia::type::StopPoint*> stop_points;

    const navitia::type::StopPointConnection* connection;

    ItemType type;

    PathItem(ItemType t = ItemType::public_transport,
             boost::posix_time::ptime departure = boost::posix_time::pos_infin,
             boost::posix_time::ptime arrival = boost::posix_time::pos_infin) :
        arrival(arrival), departure(departure), type(t) {
    }

    std::string print() const;

    const navitia::type::VehicleJourney* get_vj() const {
        if (stop_times.empty())
            return nullptr;
        return stop_times.front()->vehicle_journey;
    }
};

/** Un itinéraire complet */
struct Path {
    navitia::time_duration duration = boost::posix_time::pos_infin;
    uint32_t nb_changes = std::numeric_limits<uint32_t>::max();
    boost::posix_time::ptime request_time = boost::posix_time::pos_infin;
    std::vector<PathItem> items;
    type::EntryPoint origin;

    void print() const {
        for(auto item : items)
            std::cout << item.print() << std::endl;
    }

};

bool operator==(const PathItem & a, const PathItem & b);

/**
 * Choose if we must use a crowfly or a streetnework for a section. This function is call for the first and last section of a journey
 *
 * @param point: the object where we are going/coming: the requested origin for the first section or the destination for the last section
 * @param stop_point: for the first section, the stop point where we are going, or for the last section the stop point from where we come
 */
bool use_crow_fly(const type::EntryPoint& point, const type::StopPoint* stop_point, const type::Data& data);


}}



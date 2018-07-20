import json
from sfsimodels.models import soils, buildings, foundations, material, systems
from collections import OrderedDict
from sfsimodels import models
from sfsimodels.exceptions import deprecation, ModelError


def add_to_obj(obj, dictionary, exceptions=[], verbose=0):
    """
    Cycles through a dictionary and adds the key-value pairs to an object.

    :param obj:
    :param dictionary:
    :param exceptions:
    :param verbose:
    :return:
    """
    for item in dictionary:
        if item in exceptions:
            continue
        if dictionary[item] is not None:
            if verbose:
                print("assign: ", item, dictionary[item])
            setattr(obj, item, dictionary[item])


def load_json(ffp, verbose=0):
    """
    Given a json file it creates a dictionary of sfsi objects

    :param ffp: str, Full file path to json file
    :param verbose: int, console output
    :return: dict
    """
    data = json.load(open(ffp))
    return ecp_dict_to_objects(data, verbose=verbose)


def loads_json(p_str, verbose=0):
    data = json.loads(p_str)
    return ecp_dict_to_objects(data, verbose=verbose)


# Deprecated name
def dicts_to_objects(data, verbose=0):
    """Deprecated. Use ecp_dict_to_objects"""
    deprecation('Deprecated, dicts_to_objects should be switched to ecp_dict_to_objects')
    ecp_dict_to_objects(data, verbose=verbose)


def ecp_dict_to_objects(ecp_dict, verbose=0):
    """
    Given an ecp dictionary, build a dictionary of sfsi objects

    :param ecp_dict: dict, engineering consistency project dictionary
    :param verbose: int, console output
    :return: dict
    """

    data_models = ecp_dict["models"]
    soil_objs = {}
    soil_profile_objs = {}
    foundation_objs = {}
    building_objs = {}
    system_objs = {}
    if "soils" in data_models:
        for m_id in data_models["soils"]:
            new_soil = soils.Soil()
            add_to_obj(new_soil, data_models["soils"][m_id], verbose=verbose)
            soil_objs[int(data_models["soils"][m_id]["id"])] = new_soil

    if "soil_profiles" in data_models:
        for m_id in data_models["soil_profiles"]:
            new_soil_profile = soils.SoilProfile()
            new_soil_profile.id = data_models["soil_profiles"][m_id]["id"]
            for j in range(len(data_models["soil_profiles"][m_id]["layers"])):
                depth = data_models["soil_profiles"][m_id]['layers'][j]["depth"]
                soil = soil_objs[int(data_models["soil_profiles"][m_id]['layers'][j]["soil_id"])]
                new_soil_profile.add_layer(depth, soil)
            add_to_obj(new_soil_profile, data_models["soil_profiles"][m_id], exceptions=["layers"], verbose=verbose)
            soil_profile_objs[int(data_models["soil_profiles"][m_id]["id"])] = new_soil_profile

    if "foundations" in data_models:
        for m_id in data_models["foundations"]:
            if data_models["foundations"][m_id]["type"] == "raft":
                new_foundation = foundations.RaftFoundation()
            elif data_models["foundations"][m_id]["type"] == "pad":
                new_foundation = foundations.PadFoundation()
            else:
                new_foundation = foundations.Foundation()
            new_foundation.id = data_models["foundations"][m_id]["id"]
            add_to_obj(new_foundation, data_models["foundations"][m_id], verbose=verbose)
            foundation_objs[int(data_models["foundations"][m_id]["id"])] = new_foundation

    if "buildings" in data_models:
        for m_id in data_models["buildings"]:
            if data_models["buildings"][m_id]["type"] == "structure":
                new_building = buildings.Structure()
            elif data_models["buildings"][m_id]["type"] == "building":
                new_building = buildings.Building()
            else:
                new_building = buildings.Building()
            add_to_obj(new_building, data_models["buildings"][m_id], verbose=verbose)
            building_objs[int(data_models["buildings"][m_id]["id"])] = new_building
    if "systems" in data_models:
        for m_id in data_models["systems"]:
            new_system = systems.SoilStructureSystem()
            add_to_obj(new_system, data_models["systems"][m_id], verbose=verbose)
            system_objs[int(data_models["systems"][m_id]["id"])] = new_system

    objs = {
        "soils": soil_objs,
        "soil_profiles": soil_profile_objs,
        "foundations": foundation_objs,
        "buildings": building_objs,
        "systems": system_objs,

    }

    return objs


class Output(object):
    name = ""
    units = ""
    doi = ""
    sfsimodels_version = ""
    comments = ""

    def __init__(self):
        self.models = OrderedDict([("soils", OrderedDict()),
                            ("soil_profiles", OrderedDict()),
                            ("foundations", OrderedDict()),
                            ("buildings", OrderedDict()),
                            ("systems", OrderedDict()),
                            ])

    def add_to_dict(self, an_object, extras={}):
        """
        Convert models to json serialisable output

        :param an_object: An instance of a model object
        :param extras: A dictionary of extra variables that should be
        :return:
        """
        if an_object.id is None:
            raise ModelError("id must be set on object before adding to output.")
        if isinstance(an_object, models.Soil):
            self.models["soils"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.SoilProfile):
            profile_dict = an_object.to_dict()
            profile_dict["layers"] = []
            for layer in an_object.layers:
                self.models["soils"][an_object.layers[layer].id] = an_object.layers[layer].to_dict()
                profile_dict["layers"].append({
                    "soil_id": str(an_object.layers[layer].id),
                    "depth": float(layer)
                })

            self.models["soil_profiles"][an_object.id] = profile_dict
        elif isinstance(an_object, models.Foundation):
            self.models["foundations"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.Structure):
            self.models["buildings"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.Building):
            self.models["buildings"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.SoilStructureSystem):
            self.models["systems"][an_object.id] = an_object.to_dict()
        elif hasattr(an_object, "to_dict"):  # Catch any custom objects
            if hasattr(an_object, "type"):
                mtype = an_object.type
                if mtype not in self.models:
                    self.models[mtype] = OrderedDict()
                self.models[mtype][an_object.id] = an_object.to_dict()
                self.models["systems"][an_object.id] = an_object.to_dict()
            else:
                raise ModelError("Object does not have attribute 'type', cannot add to output.")
        else:
            raise ModelError("Object does not have method 'to_dict', cannot add to output.")

    def add_to_output(self, mtype, m_id, serialisable_dict):
        """
        Can add additional objects or dictionaries to output file that don't conform to standard objects.

        :param mtype:
        :param m_id:
        :param serialisable_dict:
        :return:
        """
        if mtype not in self.models:
            self.models[mtype] = OrderedDict()
        self.models[mtype][m_id] = serialisable_dict


    @staticmethod
    def parameters():
        return ["name", "units", "doi", "sfsimodels_version", "comments", "models"]

    def to_dict(self):
        outputs = OrderedDict()
        for item in self.parameters():
            outputs[item] = self.__getattribute__(item)
        return outputs

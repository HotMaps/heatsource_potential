import os

CELERY_BROKER_URL_DOCKER = "amqp://admin:mypass@rabbit:5672/"
CELERY_BROKER_URL_LOCAL = "amqp://localhost/"


CM_REGISTER_Q = "rpc_queue_CM_register"  # Do no change this value

CM_NAME = "CM - Heat sources potential"
RPC_CM_ALIVE = "rpc_queue_CM_ALIVE"  # Do no change this value
RPC_Q = "rpc_queue_CM_compute"  # Do no change this value
CM_ID = 11  # CM_ID is defined by the enegy research center of Martigny (CREM)
PORT_LOCAL = int("500" + str(CM_ID))
PORT_DOCKER = 80

# TODO ********************setup this URL depending on which version you are running***************************

CELERY_BROKER_URL = CELERY_BROKER_URL_DOCKER
PORT = PORT_DOCKER

# TODO ********************setup this URL depending on which version you are running***************************

TRANFER_PROTOCOLE = "http://"
INPUTS_CALCULATION_MODULE = [
    {
        "input_name": "Maximum distance to consider the heat source within the urban areas",
        "input_type": "input",
        "input_parameter_name": "within_dist",
        "input_value": "150",
        "input_priority": 0,
        "input_unit": "m",
        "input_min": 50,
        "input_max": 2000,
        "cm_id": CM_ID,  # Do no change this value
    },
    {
        "input_name": "Maximum distance to consider the heat source near the urban areas, all the areas above this threshold will be classified as far from the urban areas",
        "input_type": "input",
        "input_parameter_name": "near_dist",
        "input_value": "1000",
        "input_priority": 0,
        "input_unit": "m",
        "input_min": 200,
        "input_max": 10000,
        "cm_id": CM_ID,  # Do no change this value
    },
]

WIKIURL = os.environ.get("WIKIURL", "https://wiki.hotmaps.eu/en/")

SIGNATURE = {
    "category": "Supply",
    "authorized_scale": ["NUTS 3", "NUTS 2", "NUTS 0", "LAU 2"],
    "cm_name": CM_NAME,
    "layers_needed": [
        # "urban areas" or "corine land cover",
    ],
    "type_layer_needed": [],
    "vectors_needed": [],
    # vector layers should be added here
    "type_vectors_needed": [
        #"wwtp",
    ],
    "cm_url": "Do not add something",
    "cm_description": "This computation module calculates the potential of waste water treatment plants that can be utilized in the selected area",
    "cm_id": CM_ID,
    "wiki_url": WIKIURL + "CM-Heat-source-potential",
    "inputs_calculation_module": INPUTS_CALCULATION_MODULE,
}

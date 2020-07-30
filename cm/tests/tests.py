import os
import tempfile
import unittest

# from pprint import pprint

from app import create_app
import os.path
from shutil import copyfile
from .test_client import TestClient
from app.constant import INPUTS_CALCULATION_MODULE


# Add this check to be able to execute and debug code locally with:
# LOCAL=true python3 test.py
if os.environ.get("LOCAL", False):
    UPLOAD_DIRECTORY = os.path.join(
        tempfile.gettempdir(), "hotmaps", "cm_files_uploaded"
    )
else:
    UPLOAD_DIRECTORY = "/var/hotmaps/cm_files_uploaded"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
    os.chmod(UPLOAD_DIRECTORY, 0o777)


class TestAPI(unittest.TestCase):
    vector_test_path = os.path.join("tests", "data", "vector_for_test.json")
    vector_updir_path = os.path.join(UPLOAD_DIRECTORY, "vector_for_test.json")

    def setUp(self):
        self.app = create_app(os.environ.get("FLASK_CONFIG", "development"))
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = TestClient(self.app,)

    def tearDown(self):
        self.ctx.pop()

    def test_params_check(self):
        inputs_raster_selection = {}
        inputs_parameter_selection = {}
        inputs_vector_selection = {}
        inputs_parameter_selection["within_dist"] = 1000  # m
        inputs_parameter_selection["near_dist"] = 100  # m

        # register the calculation module a
        payload = {
            "inputs_raster_selection": inputs_raster_selection,
            "inputs_parameter_selection": inputs_parameter_selection,
            "inputs_vector_selection": inputs_vector_selection,
        }

        rv, json = self.client.post("computation-module/compute/", data=payload)

        self.assertTrue(rv.status_code == 200)
        # check we have just one indicator the warning
        self.assertEqual(
            len(json["result"]["indicator"]), 1, msg="More than a worning is present"
        )

        # check the content of the warning
        warning = json["result"]["indicator"][0]
        self.assertEqual(
            warning["name"],
            "near distance limit (100) <= within distance limit (1000), please correct the values and try again",
        )

    # def test_computaion(self):
    #     inputs_raster_selection = {}
    #     inputs_parameter_selection = {}
    #     inputs_vector_selection = {}
    #     inputs_parameter_selection["within_dist"] = 150  # m
    #     inputs_parameter_selection["near_dist"] = 1000  # m

    #     # register the calculation module a
    #     payload = {
    #         "inputs_raster_selection": inputs_raster_selection,
    #         "inputs_parameter_selection": inputs_parameter_selection,
    #         "inputs_vector_selection": inputs_vector_selection,
    #     }

    #     rv, json = self.client.post("computation-module/compute/", data=payload)

    #     self.assertTrue(rv.status_code == 200)
    #     # check we have no indicators
    #     self.assertEqual(len(json["result"]["indicator"]), 0)

    #     self.assertEqual(
    #         len(json["result"]["vector_layers"]),
    #         1,
    #         msg="The module did not produce the results",
    #     )

    #     # check the content of the warning
    #     vect = json["result"]["vector_layers"][0]
    #     self.assertEqual(vect[-4:], ".zip")

import logging
import re
import unittest

import numpy as np

from kynetix.model import KineticModel
from kynetix.solvers import *

from unit_test import *


class KMCTOFPluginTest(unittest.TestCase):

    def setUp(self):
        # Test case setting.
        self.maxDiff = None
        self.setup = kmc_path + "/kmc_tof_plugin.mkm"

    def test_run_with_tof(self):
        " Make sure KMCSolver object can be constructed correctly. "
        model = KineticModel(setup_file=self.setup, verbosity=logging.WARNING)
        parser = model.parser()
        parser.parse_data(filename=kmc_energy, relative=True)
        
        # Run the model with analysis.
        model.run_kmc(processes_file=kmc_processes,
                      configuration_file=kmc_config,
                      sitesmap_file=kmc_sites)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(KMCTOFPluginTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

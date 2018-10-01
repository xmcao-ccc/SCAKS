import unittest

from .chem_formula_test import ChemFormulaTest
from .chem_state_test import ChemStateTest
from .parser_base_test import ParserBaseTest
from .relative_energy_parser_test import RelativeEnergyParserTest
from .absolute_energy_parser_test import AbsoluteEnergyParserTest
from .kmc_parser_test import KMCParserTest


def suite():
    suite = unittest.TestSuite(
        [unittest.TestLoader().loadTestsFromTestCase(ChemFormulaTest),
         unittest.TestLoader().loadTestsFromTestCase(ChemStateTest),
         unittest.TestLoader().loadTestsFromTestCase(ParserBaseTest),
         unittest.TestLoader().loadTestsFromTestCase(RelativeEnergyParserTest),
         unittest.TestLoader().loadTestsFromTestCase(AbsoluteEnergyParserTest),
         unittest.TestLoader().loadTestsFromTestCase(KMCParserTest)]
    )
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

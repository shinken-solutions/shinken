

from os.path import abspath, dirname, join

from shinken_test import unittest, ShinkenTest

from shinken.objects.module import Module
from shinken.modulesmanager import ModulesManager



modules_dir = join(dirname(abspath(__file__)), 'test_module_as_package')

class TestModuleManager_And_Packages(ShinkenTest):
    ''' Test to make sure that we correctly import shinken modules.
    '''

    def test_conflicting_modules(self):

        # prepare 2 modconfs:
        modconfA = Module({'module_name': 'whatever', 'module_type': 'modA'})
        modconfB = Module({'module_name': '42',       'module_type': 'modB'})

        mods = (modconfA, modconfB)

        mm = self.modulemanager = ModulesManager('broker', modules_dir, mods)
        mm.load_and_init()

        for mod in mm.imported_modules:
            self.assertEqual(mod.expected_helpers_X, mod.helpers.X)

        mod1, mod2 = mm.imported_modules
        self.assertNotEqual(mod1.helpers.X, mod2.helpers.X)



if __name__ == '__main__':
    unittest.main()


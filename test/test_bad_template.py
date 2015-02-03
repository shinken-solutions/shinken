
from shinken_test import ShinkenTest


class TestConfig(ShinkenTest):

    def setUp(self):
        pass # force no setUp for this class.

    def test_bad_template_use_itself(self):
        self.setup_with_file('etc/bad_template_use_itself.cfg')
        self.assertIn(u"Host u'bla' use/inherits from itself ! Imported from: etc/bad_template_use_itself.cfg:1",
                      self.conf.hosts.configuration_errors)

    def test_bad_host_use_undefined_template(self):
        self.setup_with_file('etc/bad_host_use_undefined_template.cfg')
        self.assertIn(u"Host u'bla' use/inherit from an unknown template (u'undefined') ! Imported from: etc/bad_host_use_undefined_template.cfg:2",
                      self.conf.hosts.configuration_warnings)

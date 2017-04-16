


from shinken_test import *


class Test_CheckResult_Brok(ShinkenTest):

    cfg_file = 'etc/shinken_1r_1h_1s.cfg'

    expected_host_command_name = 'check-host-alive-parent'
    expected_svc_command_name = 'check_service'

    def setUp(self):
        self.setup_with_file(self.cfg_file)

    def test_host_check_result_brok_has_command_name(self):
        host = self.sched.hosts.find_by_name('test_host_0')
        res = {}
        host.fill_data_brok_from(res, 'check_result')
        self.assertIn('command_name', res)
        self.assertEqual(self.expected_host_command_name, res['command_name'])

    def test_service_check_result_brok_has_command_name(self):
        svc = self.sched.services.find_srv_by_name_and_hostname(
            'test_host_0', 'test_ok_0')
        res = {}
        svc.fill_data_brok_from(res, 'check_result')
        self.assertIn('command_name', res)
        self.assertEqual(self.expected_svc_command_name, res['command_name'])


class Test_CheckResult_Brok_Host_No_command(Test_CheckResult_Brok):

    cfg_file = 'etc/shinken_host_without_cmd.cfg'

    expected_host_command_name = "_internal_host_up"

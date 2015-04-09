#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#
# This file is used to test reading and processing of config files
#

import mock

from shinken_test import *
from shinken.misc import regenerator
from shinken import brok
from shinken.objects import item

class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest
    def _get_update_broker_brok(self):
        b = brok.Brok('update_broker_status', {'broker_name': 'broker-master'})
        b.prepare()
        return b

    def _get_update_scheduler_brok(self):
        b = brok.Brok('update_scheduler_status', {'scheduler_name':
                                                      'scheduler-master'})
        b.prepare()
        return b

    def _get_update_poller_brok(self):
        b = brok.Brok('update_poller_status', {'poller_name': 'poller-master'})
        b.prepare()
        return b

    def _get_update_receiver_brok(self):
        b = brok.Brok('update_receiver_status', {'receiver_name':
                                                     'receiver-master'})
        b.prepare()
        return b

    def _get_update_reactionner_brok(self):
        b = brok.Brok('update_reactionner_status',
                      {'reactionner_name':'reactionner-master'})
        b.prepare()
        return b

    def test_manage_update_broker_status_brok_with_broker_restart(self):
        with mock.patch.object(regenerator.Regenerator,
                               'manage_initial_broker_status_brok',
                               return_value=None) as \
                mock_manage_initial_broker_status_brok:
            with mock.patch.object(regenerator.Regenerator,
                                   'update_element', return_value=None):
                b = self._get_update_broker_brok()
                reg = regenerator.Regenerator()
                reg.manage_update_broker_status_brok(b)
        mock_manage_initial_broker_status_brok.assert_called_once_with(b)

    def test_manage_update_broker_status_brok_with_broker_normally(self):
        with mock.patch.object(regenerator.Regenerator,
                               'manage_initial_broker_status_brok',
                               return_value=None) as \
                mock_manage_initial_broker_status_brok:
            with mock.patch.object(regenerator.Regenerator,
                                   'update_element', return_value=None) \
                    as mock_update_element:
                b = self._get_update_broker_brok()
                with mock.patch.object(item.Items, 'index_item',
                                       return_value=b.data):
                    reg = regenerator.Regenerator()
                    original_info = {}
                    reg.brokers[b.data['broker_name']] = original_info
                    reg.manage_update_broker_status_brok(b)
        mock_update_element.assert_called_once_with(original_info, b.data)
        with self.assertRaises(AssertionError):
            mock_manage_initial_broker_status_brok.assert_called_once_with(b)

    def test_manage_update_scheduler_status_brok_with_broker_restart(self):
        with mock.patch.object(regenerator.Regenerator,
                               'manage_initial_scheduler_status_brok',
                               return_value=None) as \
                mock_manage_initial_scheduler_status_brok:
            with mock.patch.object(regenerator.Regenerator,
                                   'update_element', return_value=None):
                b = self._get_update_scheduler_brok()
                reg = regenerator.Regenerator()
                reg.manage_update_scheduler_status_brok(b)
        mock_manage_initial_scheduler_status_brok.assert_called_once_with(b)

    def test_manage_update_scheduler_status_brok_with_broker_normally(self):
        with mock.patch.object(regenerator.Regenerator,
                               'manage_initial_scheduler_status_brok',
                               return_value=None) as \
                mock_manage_initial_scheduler_status_brok:
            with mock.patch.object(regenerator.Regenerator,
                                   'update_element', return_value=None) \
                    as mock_update_element:
                b = self._get_update_scheduler_brok()
                with mock.patch.object(item.Items, 'index_item',
                                       return_value=b.data):
                    reg = regenerator.Regenerator()
                    original_info = {}
                    reg.schedulers[b.data['scheduler_name']] = original_info
                    reg.manage_update_scheduler_status_brok(b)
        mock_update_element.assert_called_once_with(original_info, b.data)
        with self.assertRaises(AssertionError):
            mock_manage_initial_scheduler_status_brok.assert_called_once_with(b)

    def test_manage_update_poller_status_brok_with_broker_restart(self):
        with mock.patch.object(regenerator.Regenerator,
                               'manage_initial_poller_status_brok',
                               return_value=None) as \
                mock_manage_initial_poller_status_brok:
            with mock.patch.object(regenerator.Regenerator,
                                   'update_element', return_value=None):
                b = self._get_update_poller_brok()
                reg = regenerator.Regenerator()
                reg.manage_update_poller_status_brok(b)
        mock_manage_initial_poller_status_brok.assert_called_once_with(b)

    def test_manage_update_poller_status_brok_with_broker_normally(self):
        with mock.patch.object(regenerator.Regenerator,
                               'manage_initial_poller_status_brok',
                               return_value=None) as \
                mock_manage_initial_poller_status_brok:
            with mock.patch.object(regenerator.Regenerator,
                                   'update_element', return_value=None) \
                    as mock_update_element:
                b = self._get_update_poller_brok()
                with mock.patch.object(item.Items, 'index_item',
                                       return_value=b.data):
                    reg = regenerator.Regenerator()
                    original_info = {}
                    reg.pollers[b.data['poller_name']] = original_info
                    reg.manage_update_poller_status_brok(b)
        mock_update_element.assert_called_once_with(original_info, b.data)
        with self.assertRaises(AssertionError):
            mock_manage_initial_poller_status_brok.assert_called_once_with(b)

    def test_manage_update_receiver_status_brok_with_broker_restart(self):
        with mock.patch.object(regenerator.Regenerator,
                               'manage_initial_receiver_status_brok',
                               return_value=None) as \
                mock_manage_initial_receiver_status_brok:
            with mock.patch.object(regenerator.Regenerator,
                                   'update_element', return_value=None):
                b = self._get_update_receiver_brok()
                reg = regenerator.Regenerator()
                reg.manage_update_receiver_status_brok(b)
        mock_manage_initial_receiver_status_brok.assert_called_once_with(b)

    def test_manage_update_receiver_status_brok_with_broker_normally(self):
        with mock.patch.object(regenerator.Regenerator,
                               'manage_initial_receiver_status_brok',
                               return_value=None) as \
                mock_manage_initial_receiver_status_brok:
            with mock.patch.object(regenerator.Regenerator,
                                   'update_element', return_value=None) \
                    as mock_update_element:
                b = self._get_update_receiver_brok()
                with mock.patch.object(item.Items, 'index_item',
                                       return_value=b.data):
                    reg = regenerator.Regenerator()
                    original_info = {}
                    reg.receivers[b.data['receiver_name']] = original_info
                    reg.manage_update_receiver_status_brok(b)
        mock_update_element.assert_called_once_with(original_info, b.data)
        with self.assertRaises(AssertionError):
            mock_manage_initial_receiver_status_brok.assert_called_once_with(b)

    def test_manage_update_reactionner_status_brok_with_broker_restart(self):
        with mock.patch.object(regenerator.Regenerator,
                               'manage_initial_reactionner_status_brok',
                               return_value=None) as \
                mock_manage_initial_reactionner_status_brok:
            with mock.patch.object(regenerator.Regenerator,
                                   'update_element', return_value=None):
                b = self._get_update_reactionner_brok()
                reg = regenerator.Regenerator()
                reg.manage_update_reactionner_status_brok(b)
        mock_manage_initial_reactionner_status_brok.assert_called_once_with(b)

    def test_manage_update_reactionner_status_brok_with_broker_normally(self):
        with mock.patch.object(regenerator.Regenerator,
                               'manage_initial_reactionner_status_brok',
                               return_value=None) as \
                mock_manage_initial_reactionner_status_brok:
            with mock.patch.object(regenerator.Regenerator,
                                   'update_element', return_value=None) \
                    as mock_update_element:
                b = self._get_update_reactionner_brok()
                with mock.patch.object(item.Items, 'index_item',
                                       return_value=b.data):
                    reg = regenerator.Regenerator()
                    original_info = {}
                    reg.reactionners[b.data['reactionner_name']] = original_info
                    reg.manage_update_reactionner_status_brok(b)
        mock_update_element.assert_called_once_with(original_info, b.data)
        with self.assertRaises(AssertionError):
            mock_manage_initial_reactionner_status_brok\
                .assert_called_once_with(b)

if __name__ == '__main__':
    unittest.main()

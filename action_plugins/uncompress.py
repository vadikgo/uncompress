# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Dylan Martin <dmartin@seattlecentral.edu>
# (c) 2015, Jonathan Mainguy <jon@soh.re>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        ''' handler for uncompress operations '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        source = self._task.args.get('src', None)
        dest = self._task.args.get('dest', None)
        copy = boolean(self._task.args.get('copy', True))

        if source is None or dest is None:
            result['failed'] = True
            result['msg'] = "src (or content) and dest are required"
            return result

        remote_user = task_vars.get('ansible_ssh_user') or self._play_context.remote_user
        if not tmp:
            tmp = self._make_tmp_path(remote_user)

        dname, junk = os.path.split(dest)
        dest = self._remote_expand_user(dname)
        source = os.path.expanduser(source)

        if copy:
            if self._task._role is not None:
                source = self._loader.path_dwim_relative(self._task._role._role_path, 'files', source)
            else:
                source = self._loader.path_dwim_relative(self._loader.get_basedir(), 'files', source)

        remote_checksum = self._remote_checksum(dest, all_vars=task_vars)
        if remote_checksum != '3':
            result['failed'] = True
            result['msg'] = "dest '%s' must be an existing dir" % dest
            return result
        elif remote_checksum == '4':
            result['failed'] = True
            result['msg'] = "python isn't present on the system.  Unable to compute checksum"
            return result

        if copy:
            # transfer the file to a remote tmp location
            junk, fname = os.path.split(source)
            tmp_src = tmp + fname
            self._connection.put_file(source, tmp_src)

        # handle diff mode client side
        # handle check mode client side
        # fix file permissions when the copy is done as a different user
        if copy:
            if self._play_context.become and self._play_context.become_user != 'root':
                if not self._play_context.check_mode:
                    self._remote_chmod('a+r', tmp_src)

            # Build temporary module_args.
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    src=tmp_src,
                    original_basename=os.path.basename(source),
                ),
            )

        else:
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    original_basename=os.path.basename(source),
                ),
            )

        # execute the uncompress module now, with the updated args
        result.update(self._execute_module(module_args=new_module_args, task_vars=task_vars))
        return result

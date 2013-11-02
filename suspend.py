# -*- coding: utf-8 -*-
#
# suspend.py
#
# Copyright (C) 2012 - fossfreedom
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# The Rhythmbox authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and Rhythmbox. This permission is above and beyond the permissions granted
# by the GPL license by which Rhythmbox is covered. If you modify this code
# you may extend this exception to your version of the code, but you are not
# obligated to do so. If you do not wish to do so, delete this exception
# statement from your version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.


from gi.repository import GObject
from gi.repository import GConf
#from gi.repository import RB
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Peas
from gi.repository import PeasGtk

#import rb
import dbus
import os

from threading import Thread
import threading
import time

GLib.threads_init()
from suspend_rb3compat import ActionGroup
from suspend_rb3compat import Action
from suspend_rb3compat import ApplicationShell

ui_str = \
"""<ui>
    <menubar name="MenuBar">
        <menu name="ControlMenu" action="Control">
            <menuitem name="Poweroff" action="PowerOffAction"/>
        </menu>
    </menubar>
</ui>"""

GCONF_DIR = '/apps/rhythmbox/plugins/suspend'
GCONF_KEYS = {
    'action': GCONF_DIR + '/action',
    'time': GCONF_DIR + '/time'
}

DIALOG_FILE = 'suspend.glade'
DIALOG = 'config_dialog'

class SuspendConfigDialog(GObject.Object, PeasGtk.Configurable):
    __type_name__ = 'SuspendConfigDialog'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        print("__init__")
        GObject.Object.__init__(self)
        self.gconf = GConf.Client.get_default()
        
    def do_create_configure_widget(self):
        print("do_create_configure_widget")
        self.builder = Gtk.Builder()
        ui_file = os.path.dirname(__file__) + "/" + DIALOG_FILE 
        #rb.find_plugin_file( self, DIALOG_FILE ) this should find the fine by instead returns None - dont know why
        print(ui_file)
        self.builder.add_from_file(ui_file)

        content = self.builder.get_object("dialog-vbox1")
        
        # combo
        combo = self.builder.get_object("cmbAction")
        
        model = Gtk.ListStore(GObject.TYPE_STRING)
        model.append(["Power Off"])
        model.append(["Suspend"])
        combo.set_model(model)
        combo.set_active(self.gconf.get_int(GCONF_KEYS['action']))
        cell = Gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, "text", 0)
    
        self.combo = combo
        
        #text
        textTime = self.builder.get_object('textTime')
        textTime.set_text(str(self.gconf.get_string(GCONF_KEYS['time'])))
        self.textTime = textTime
        
        #put content
#       self.get_content_area().add(content)
#       self.add_action_widget(Gtk.Button(stock=Gtk.StockType.CLOSE), 0)

        #signals        
        combo.connect('changed', self.action_changed_cb)
        textTime.connect('changed', self.action_changed_time)
#       self.builder.connect('response', self.close_cb)


#       self.show_all()
        return self.builder.get_object( DIALOG )
        
    
    def action_changed_cb(self, combo):
        v = combo.get_active()
        print("mode changed to %d" % v)
        self.gconf.set_int(GCONF_KEYS['action'], v)
        
#   def close_cb(self, widget, event):
#       self.gconf.set_int(GCONF_KEYS['action'], self.combo.get_active())
#       self.gconf.set_string(GCONF_KEYS['time'], self.textTime.get_text())
#       print 'close', self.textTime.get_text()
    def action_changed_time(self, textTime):
        self.gconf.set_string(GCONF_KEYS['time'], self.textTime.get_text())
        print('time', self.textTime.get_text())

#d = SuspendConfigDialog()
#d.run()

GObject.type_register(SuspendConfigDialog)


class SuspendPlugin(GObject.GObject, Peas.Activatable):
    __gtype_name__ = 'SuspendPlugin'
    object = GObject.Property(type=GObject.GObject)

    def __init__(self):
        super(SuspendPlugin, self).__init__()
        self.gconf = GConf.Client.get_default()
        self.window = None
        self.poweroff = False
        self.config_dialog = None
        self.dialog = None
        
        self.gconf.add_dir(GCONF_DIR, preload=False)
        userdata=None
        self.gconf.notify_add(GCONF_KEYS['action'], self.action_changed_cb, userdata)
        self.gconf.notify_add(GCONF_KEYS['time'], self.time_changed_cb, userdata)
        
        self.poweroff_time = 60
        self.poweroff_action = 1 # 0 - poweroff, 1 - suspend
        self.poweroff_action_dict = { 0: 'Shutdown', 1: 'Suspend' }
        self.poweroff_action_func = {0: self.action_shutdown, 1: self.action_suspend}
        
        self.is_playing = False
        
    def do_activate(self):
        self.shell = self.object
        
        self.action_group = ActionGroup(self.shell, 'PowerOffActionGroup')
        action = self.action_group.add_action(func=self.set_poweroff,
            action_name='PowerOffAction', label='PowerOff',
            action_type='app', action_state=ActionGroup.TOGGLE)

        self._appshell = ApplicationShell(self.shell)
        self._appshell.insert_action_group(self.action_group)
        self._appshell.add_app_menuitems(ui_str, 'PowerOffActionGroup')
        
        ## bind to signal, end of playlist
        self.shell_player = self.shell.props.shell_player
        self.player_connect_id = self.shell_player.connect('playing-changed', self.playing_changed)
        
        self.load_config()
        
    def do_deactivate(self):
        self._appshell.cleanup()
        self.shell_player.disconnect(self.player_connect_id)
        if self.dialog:
            self.dialog.destroy()
    
    def action_changed_cb(self, client, id, entry, d):
        gaction = self.gconf.get_int(GCONF_KEYS['action'])
        self.poweroff_action = gaction
    
    def time_changed_cb(self, client, id, entry, d):
        gtime = self.gconf.get_string(GCONF_KEYS['time'])
        self.poweroff_time = gtime
    
    def load_config(self):
        gtime = self.gconf.get_string(GCONF_KEYS['time'])
        gaction = self.gconf.get_int(GCONF_KEYS['action'])
        if gtime == None:
            gtime = 60
        else:
            gtime = int(gtime)
        
        if gaction not in [0,1]:
            gaction = 1
        
        self.poweroff_time = gtime
        self.poweroff_action = gaction
    
    def set_poweroff(self, *args):
        #btn = self.ui.get_widget('/ToolBar/PowerOff')
        
        if self.poweroff:
            self.poweroff = False
            #btn.set_tooltip_text(_("%s computer after playlist end [is OFF]" % (self.poweroff_action_dict[self.poweroff_action])))
        else:
            self.poweroff = True
            #btn.set_tooltip_text(_("%s computer after playlist end [is ON]" % (self.poweroff_action_dict[self.poweroff_action])))
    
    def action_suspend(self):
        bus = dbus.SystemBus()
        proxy = bus.get_object('org.freedesktop.UPower', '/org/freedesktop/UPower')
        iface = dbus.Interface(proxy, 'org.freedesktop.UPower')
        ret = iface.Suspend()
        print('POWER OFF', ret)
        self.dialog.destroy()
    
    def action_shutdown(self):
        bus = dbus.SystemBus()
        proxy = bus.get_object('org.freedesktop.ConsoleKit', '/org/freedesktop/ConsoleKit/Manager')
        iface = dbus.Interface(proxy, 'org.freedesktop.ConsoleKit.Manager')
        iface.Stop()
        print('SHUTDOWN')
        self.dialog.destroy()
    
    def playing_changed(self, player, playing):
        
        if not self.is_playing and playing:
            self.is_playing = True
        
        if not playing and self.poweroff and self.is_playing:
            self.dialog = Gtk.MessageDialog(type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.CANCEL, message_format=_("Computer will be %s after %d seconds. You can cancel this procedure now." % (self.poweroff_action_dict[self.poweroff_action], int(self.poweroff_time))))            
            timer = threading.Timer(int(self.poweroff_time), self.poweroff_action_func[int(self.poweroff_action)])
            timer.start()
            
            response = self.dialog.run()
            if response == Gtk.ResponseType.CANCEL:
                timer.cancel()
                print('cancel')
                self.is_playing = False
                
            self.dialog.destroy()
            
    def create_configure_dialog(self, dialog=None):
        if self.config_dialog is None:
            self.config_dialog = config.SuspendConfigDialog(self)
            self.config_dialog.connect('response', self.config_dialog_response_cb)
            
        self.config_dialog.present()
        return self.config_dialog
    
    def config_dialog_response_cb(self, dialog, response):
        print('response cb')
        dialog.hide()
# ex:noet:ts=8:

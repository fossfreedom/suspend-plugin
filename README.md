suspend-plugin
==============

Enable Rhythmbox to suspend/shutdown your computer at the end of playing from the queue or playlist

To use:

 1. set the plugin preferences option to either poweroff or suspend.

 2. For RB2.96 - 2.98 - enable the menu option Control - Poweroff to activate the plugin
 
 3. For RB2.99 and later - enable the menu option View - Powerof to activate the plugin
 
 4. Play your music from the playqueue or playlist.  At the end of the queue, a dialog will be displayed with a countdown.  
 you can either, ignore the dialog and the computer will suspend/poweroff or interrupt the process.

##GTK3 Author

 - fossfreedom <foss.freedom@gmail.com>, website - https://github.com/fossfreedom

[![Flattr Button](http://api.flattr.com/button/button-compact-static-100x17.png "Flattr This!")](https://flattr.com/thing/1237284/fossfreedomsuspend-plugin-on-GitHub "fossfreedom")  [![paypaldonate](https://www.paypalobjects.com/en_GB/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=KBV682WJ3BDGL)

------------

Use the plugin preferences to set the timeout and also whether to
shutdown (default) or to suspend your computer

Ubuntu 12.04 notes:

packages required to be installed:

    sudo apt-get install gir1.2-gconf-2.0 python-lxml

Installation:

    git clone https://github.com/fossfreedom/suspend-plugin
    cd suspend-plugin

for rhythmbox 2.96 to 2.99.1

<code>
./install.sh
</code>

for rhythbox 3.0 and later

<code>
./install.sh --rb3
</code>

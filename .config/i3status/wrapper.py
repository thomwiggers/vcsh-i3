#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script is a simple wrapper which prefixes each i3status line with custom
# information. It is a python reimplementation of:
# http://code.stapelberg.de/git/i3status/tree/contrib/wrapper.pl
#
# To use it, ensure your ~/.i3status.conf contains this line:
#     output_format = "i3bar"
# in the 'general' section.
# Then, in your ~/.i3/config, use:
#     status_command i3status | ~/i3status/contrib/wrapper.py
# In the 'bar' section.
#
# In its current version it will display the cpu frequency governor, but you
# are free to change it to display whatever you like, see the comment in the
# source code below.
#
# © 2012 Valentin Haenel <valentin.haenel@gmx.de>
# © 2015 Thom Wiggers <thom@thomwiggers.nl>
#
# This program is free software. It comes without any warranty, to the extent
# permitted by applicable law. You can redistribute it and/or modify it under
# the terms of the Do What The Fuck You Want To Public License (WTFPL), Version
# 2, as published by Sam Hocevar. See http://sam.zoy.org/wtfpl/COPYING for more
# details.

import sys
import os
import re
import json
import socket


def get_governor():
    """ Get the current governor for cpu0, assuming all CPUs use the same. """
    with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor') as fp:
        return fp.readlines()[0].strip()


def get_networkspeed():
    """Get the network traffic"""
    with os.popen('/home/thom/.config/i3status/measure-net-speed.bash') as p:
        line = p.read()

    return line


def get_mpdstatus():
    """Get the status from MPD through mpc"""
    mpd = dict(color='#36a8d5')  # nice blue
    try:
        with os.popen('mpc --host griffin') as p:
            lines = p.read().split('\n')

        if len(lines) < 3:
            mpd['color'] = '#FF0000'
            mpd['text'] = '►✖'  # |> X
            return mpd

        track = lines[0]
        paused = 'playing' not in lines[1]
        position = re.search(r'\s(\d+:\d\d/\d+:\d\d)', lines[1]).group(1)
        volume = re.search(r'volume:\s*(\d+%)', lines[2]).group(1)
    except:
        mpd['color'] = '#ee0000'
        mpd['text'] = 'ERROR'
        return mpd

    # UTF8 char is |>
    mpd['text'] = ('▐ ▌' if paused else '► {} ({}) (v: {})'
                   .format(track, position, volume))
    return mpd


def print_line(message):
    """ Non-buffered printing to stdout. """
    sys.stdout.write(message + '\n')
    sys.stdout.flush()


def read_line():
    """ Interrupted respecting reader for stdin. """
    # try reading a line, removing any extra whitespace
    try:
        line = sys.stdin.readline().strip()
        # i3status sends EOF, or an empty line
        if not line:
            sys.exit(3)
        return line
    # exit on ctrl-c
    except KeyboardInterrupt:
        sys.exit()

if __name__ == '__main__':
    # Skip the first line which contains the version header.
    print_line(read_line())

    # The second line contains the start of the infinite array.
    print_line(read_line())

    while True:
        line, prefix = read_line(), ''
        # ignore comma at start of lines
        if line.startswith(','):
            line, prefix = line[1:], ','

        j = json.loads(line)
        # insert information into the start of the json, but could be anywhere
        # CHANGE THIS LINE TO INSERT SOMETHING ELSE
        if socket.gethostname() == 'lethe':
            mpd = get_mpdstatus()
            j.insert(0, {
                'full_text': '%s' % mpd['text'],
                'name': 'mpd',
                'color': mpd['color']
            })
        j.insert(2, {
            'full_text': get_networkspeed(),
            'name': 'networkspeed'
        })
        # j.insert(4, {'full_text': '%s' % get_governor(), 'name': 'gov'})
        # and echo back new encoded json
        print_line(prefix+json.dumps(j))

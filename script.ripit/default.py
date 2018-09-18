#!/usr/bin/python -u

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import os
import re
import time
import errno
import fcntl
import signal
import traceback
import subprocess

from os.path import expanduser

ADDON = xbmcaddon.Addon()
CWD = ADDON.getAddonInfo('path').decode('utf-8')


def for_lines(buf, fn):
    i = 0
    last = 0
    n = 0
    while i < len(buf):
        # NB: CR is used to reset lines for progress report in ttys
        c = buf[i]
        if c != '\n' and c != '\r':
            i = i+1
            continue
        if last != i:
            n = n +1
            fn(buf[last:i])
        last = i+1
        i = i + 1
    return buf[last:]


def parse_line(l, progress):
    xbmc.log(l)
    if l.startswith("progress: "):
        progress.update(10 * (len(l) - 10), 'Blobbing through...')


def non_block(f):
    fd = f.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    return f


def should_stop(progress):
    return xbmc.abortRequested or progress.iscanceled()


def process_stream(f, should_stop, fn, at_end=None):
    non_block(f)
    buf = ""
    while not should_stop():
        # read more data from subprocess
        d = ""
        try:
            d = f.read(4096)
        except EnvironmentError, exc:
            if exc.errno != errno.EAGAIN:
                traceback.print_exc()
        except:
            traceback.print_exc()

        if len(d) == 0:
            if at_end is not None and at_end():
                break
            time.sleep(.2)
            continue

        buf += d
        buf = for_lines(buf, fn)


def parse_event(l, progress):
    if not re.match("sr[0-9] ", l):
        xbmc.log("invalid disk insertion event")
        return
    
    dev = "/dev/" + l[0:3]
    lbl = l[4:].replace('_', ' ').strip().title()

    if len(lbl) == 0:
        xbmc.log("invalid disk label")
        return

    xbmc.log("inserted: " + dev + " " + lbl, xbmc.LOGNOTICE)

    # create target directory
    dn = expanduser("~/Videos/" + lbl)
    try:
        os.makedirs(dn)
    except OSError, exc:
        if exc.errno != errno.EEXIST:
            raise

    dst = dn + "/" + lbl + ".mp4"
    wrk = dst + ".wrk"

    # check whether the movie already exists
    if os.path.exists(dst):
        progress.update(0, "'%s' already in collection..." % (lbl))
        subprocess.check_call(['eject', dev])
        return

    try:
        os.remove(wrk)
    except:
        pass

    progress.update(0, "Ripping '%s' from %s..." % (lbl, dev))

    # spawn HandBrakeCLI process to rip/transcode
    proc = subprocess.Popen([
        'HandBrakeCLI',
        '-i', dev,
        '--main-feature',
        '--audio-lang-list', 'eng,fra',
        '--subtitle-lang-list', 'fra,eng',
        '-f', 'av_mp4',
        '--mixdown', 'stereo',
        '-o', wrk],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    process_stream(proc.stdout,
            lambda: should_stop(progress),
            lambda l: parse_progress(l, progress, lbl),
            lambda: proc.poll() is not None)
    
    if proc.returncode is None:
        xbmc.log('terminating HandBrakeCLI process', xbmc.LOGNOTICE)
        proc.terminate()
    elif proc.returncode == 0 and os.path.exists(wrk):
        os.rename(wrk, dst)
        progress.update(0, 'Done ripping. Waiting for next disk...')
    else:
        xbmc.log('HandBrakeCLI returned %s' % (str(proc.returncode)))
        progress.update(0, 'Ripping failed. Waiting for next disk...')

    subprocess.check_call(['eject', dev])


progress_rx = None

def parse_progress(l, progress, title):
    global progress_rx

    if progress_rx is None:
        progress_rx = re.compile("Encoding: task ([0-9]+) of ([0-9]+), ([0-9]+)\\.[0-9]+ % ")

    xbmc.log(l)

    m = progress_rx.match(l)
    if m is None:
        return

    task = int(m.group(1))
    total = int(m.group(2))
    percent = int(m.group(3))

    details = l[m.end():]
    op = details.find('(')
    cp = details.find(')')
    if op != -1 and op < cp:
        details = details[op+1:cp]
    
    progress.update((task - 1) * 100 / total + percent / total, "Ripping '%s' :[CR]%s" % (title, details))


if (__name__ == '__main__'):
    progress = xbmcgui.DialogProgress()
    progress.create('RipIt', 'Waiting for disk insertion...')

    with open('/var/run/disk-inserted') as fifo:
        process_stream(fifo,
                lambda: should_stop(progress),
                lambda l: parse_event(l, progress))

    progress.close()


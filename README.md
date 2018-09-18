RipIt
=====

A simple Kodi plugin to take most of the pain out of format-shifting a DVD collection.


Requirements
------------

 * Linux: detection of disk insertion is currently based on udev rules
 * [Kodi](http://kodi.tv) for the interface
 * [HandBrakeCLI](http://handbrake.fr) for the actual ripping/encoding


Install
-------

 - Update Kodi settings to allow addons from unknown sources

 - Stop Kodi

 - Run the following commands in a terminal

    sudo make udev
    make kodi

 - Restart Kodi


Use
---

RipIt is accessed as a program add-on.

Once started, it will wait for a disk to be inserted, automatically
rip it into mp4 using HandBrakeCLI, store the output to ~/Videos,
and then eject the disk, signalling that the next one can be inserted.

It is safe to cancel the progress dialog or exit Kodi at any point,
although any progress on the current DVD will be lost.


TODO
----

 - Make output dir configurable
 - Make HandBrake options configurable
 - Make disk detection portable to other platforms


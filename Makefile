
fwrite: fwrite.c
	gcc -o fwrite fwrite.c


udev: fwrite
	cp fwrite /usr/bin/
	cp 99-ripit.rules /etc/udev/rules.d/
	rm -f /var/run/disk-inserted && mkfifo /var/run/disk-inserted
	udevadm control --reload-rules


kodi:
	cp -a script.ripit ~/.kodi/addons/
	sqlite3 ~/.kodi/userdata/Database/Addons27.db 'insert into installed select max(id)+1, "script.ripit", 1, max(installDate), NULL, NULL, "" from installed;'


.PHONY: udev kodi


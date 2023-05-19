## Requirements
* python
* pycryptodome
* win32crypt (possibly)
* Windows system
* flask
* os
* json
* requests

To run the attacker's webserver, in terminal, navigate to `Chrumiumcracker\WebApp` and run the command `python webapp.py`. The json datafiles  will be located in the `stolen_data` folder, which will be created upon running if it is non-existent.

To run the script intended for the victim, in a separate terminal, navigate to `Chrumiumcracker\Chrome` and run the command `python ChromeCracker.py`. The script will collect the stolen data from the browser and send it, using a HTTP POST request, to the attacker's webserver.
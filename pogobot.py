#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot thah look inside the database and see if the pokemon requested is appeared during the last scan
# This program is dedicated to the public domain under the CC0 license.
# First iteration made by eugenio412
# based on timerbot made inside python-telegram-bot example folder

# better on python3.4

'''please READ FIRST the README.md'''


import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3.")

from telegram.ext import Updater, CommandHandler, Job, MessageHandler, Filters
from telegram import Bot
import logging
from datetime import datetime, timezone, timedelta
import datetime as dt
import os
import errno
import json
import threading
import fnmatch
import DataSources
import Preferences
import copy
from time import sleep
from geopy.geocoders import Nominatim
import geopy
from geopy.distance import VincentyDistance

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
prefs = Preferences.UserPreferences()
jobs = dict()
geolocator = Nominatim()

# User dependant - dont add
sent = dict()
locks = dict()

# User dependant - Add to clear, addJob, loadUserConfig, saveUserConfig
#search_ids = dict()
#language = dict()
#location_ids = dict()
location_radius = 1
#pokemon:
pokemon_name = dict()
#move:
move_name = dict()

#pokemon rarity
raid_rarity = [[],
	["153","156","159","129"],
	["103","89","126","125","110"],
	["59","65","68","126","125"],
	["3","6","9","143","131","248"],
];

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def cmd_help(bot, update):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    logger.info('[%s@%s] Sending help text.' % (userName, chat_id))
    text = "*Folgende Befehle kennt der Bot:* \n\n" + \
    "/hilfe Um Hilfe zu bekommen und dieses Menü anzuzeigen \n\n" + \
    "*Pokémon:*\n\n" + \
    "/pokemon 1 \n" + \
    "Nummer des Pokémon eingeben um über dieses Benachrichtigungen zu erhalten \n" + \
    "/pokemon 1 2 3 ... \n" + \
    "Mehrfache Nummern der Pokémon können so eingegeben werden \n\n" + \
    "/raid 1 \n" + \
    "Fügt eine Gruppe von Pokémon je nach Raidlevel hinzu\n" + \
    "/entferne 1 \n" + \
    "Nummer des Pokémon löschen, wenn du über dieses nicht mehr benachrichtigt werden willst \n" + \
    "/entferne 1 2 3 ... \n" + \
    "Mehrfache Nummern der Pokémon löschen, wenn du über diese nicht mehr benachrichtigt werden willst \n\n" + \
    "*Standort:*\n\n" + \
    "Sende deinen Standort über Telegram \n" + \
    "Dies fügt einen Umkreis um deinen Standort hinzu und du erhälst Benachrichtigungen für deine Umgebung. " + \
    "Hinweis: Das senden des Standorts funktioniert nicht in Gruppen \n" +\
    "/standort xx.xx, yy.yy \n" + \
    "Sende Koordinaten als Text in der Angezeigten Form um in dem Umkreis benachrichtigt zu werden. Es kann auch" + \
    "eine Adresse eingegeben werden zum Beispiel: /standort Holstenstraße 1, 24103 Kiel oder auch /standort Kiel, DE \n" + \
    "/radius 1000 \n" + \
    "Stellt deinen Such-Radius in m (Metern) um deinen Standort herum ein \n" + \
    "/entfernestandort \n" + \
    "Lösche deinen Standort und deinen Radius. Vorsicht: Du bekommst nun Meldungen aus ganz Schleswig-Holstein! \n\n" + \
    "*Sonstiges:*\n\n" + \
    "/liste \n" + \
    "Alle Pokemon auflisten, über die du aktuell benachrichtigt wirst \n" + \
    "/speichern \n" + \
    "Speichert deine Einstellungen. *Dies ist wichtig*, damit du nach einem Neustart des Bots deine Einstellungen behälst! \n" + \
    "/laden \n" + \
    "Lade deine gespeicherten Einstellungen \n" + \
    "/status \n" + \
    "Liste deine aktuellen Einstellungen auf \n" + \
    "/ende \n" + \
    "Damit kannst du alle deine Einstellungen löschen und den Bot ausschalten. Du kannst ihn danach mit /laden " + \
    "wieder einschalten und deine Einstellungen werden geladen \n"
    bot.sendMessage(chat_id, text, parse_mode='Markdown')


def cmd_start(bot, update):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    logger.info('[%s@%s] Starting.' % (userName, chat_id))
    message = "Hallo *%s*\nDein Bot ist nun im Einstellungsmodus. *Weitere Schritte:* \n\nFalls du den Bot " + \
    "schon genutzt hast wähle /laden um deine *gespeicherten Einstellungen* zu laden.\n\nBenutzt du diesen Bot " + \
    "zum *ersten Mal*, dann füge bitte deine gewünschten *Pokémon* hinzu z.B. mit: \n*/pokemon 1* für Bisasam " + \
    "oder */pokemon 1 2 3 ...* für mehrere Pokemon über die du informiert werden willst.\n\n*Sende* anschließend " + \
    "deinen *Standort* einfach über Telegram oder nutze */standort xx.xx, yy.yy*, */standort Kiel, DE* oder " + \
    "*/standort Holstenstraße 1, 24103 Kiel* um deine Koordinaten zu senden und den Bot somit zu starten. " + \
    "(In Gruppen funktioniert das Senden des Standortes leider nicht)\n\nBitte denk daran deine Einstellungen immer zu *speichern* mit /speichern\n" + \
    "*Fahre fort mit* /hilfe *um die möglichen Befehle aufzulisten*\n"
    bot.sendMessage(chat_id, message % (userName), parse_mode='Markdown')

    # Setze default Werte und den Standort auf Kiel
    pref = prefs.get(chat_id)
    checkAndSetUserDefaults(pref)

def cmd_add(bot, update, args, job_queue):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)
    pokemon_in_raid = [153,156,159,129,103,89,126,125,110,3,6,9,94,134,135,136,3,5,6,9,143,131,248]
	
    if args != []:
        if args[0].isdigit():
            if len(args) <= 0:
                bot.sendMessage(chat_id, text='Nutzung: "/pokemon #Nummer" oder "/pokemon #Nummer1 #Nummer2 ... (Ohne #)')
                return
        else:
            bot.sendMessage(chat_id, text='Bitte nur Zahlenwerte eingeben!')
            return
    else:
        bot.sendMessage(chat_id, text='Bitte nur Zahlenwerte eingeben!')
        return
		
    for x in args:
        if int(x) > 251 or int(x) <= 0:
            bot.sendMessage(chat_id, text='Bitte keine Pokemonnummer über 251 eingeben!')
            return
        if int(x) not in pokemon_in_raid:
            bot.sendMessage(chat_id, text='Pokemon gibt es nicht im Raid!\nNutze einfach /raid 4 oder das gewünschte Raidlevel')
            return

    addJob(bot, update, job_queue)
    logger.info('[%s@%s] Add pokemon.' % (userName, chat_id))

    # Wenn nicht geladen oder mit /start gestartet wurde, dann setze ggf. auch default Werte und setze Standort auf Kiel
    loc = pref.get('location')
    if loc[0] is None or loc[1] is None:
        bot.sendMessage(chat_id, text='*Du hast keinen Standort gewählt! Du wirst nun nach Kiel gesetzt!*', parse_mode='Markdown')

    checkAndSetUserDefaults(pref)

    try:
        search = pref.get('search_ids')
        for x in args:
            if int(x) not in search:
                search.append(int(x))
        search.sort()
        pref.set('search_ids',search)
        cmd_list(bot, update)
    except Exception as e:
        logger.error('[%s@%s] %s' % (userName, chat_id, repr(e)))
        bot.sendMessage(chat_id, text='Nutzung: "/pokemon #Nummer" oder "/pokemon #Nummer1 #Nummer2 ... (Ohne #)')


def cmd_addByRarity(bot, update, args, job_queue):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)

    if args != []:
        if args[0].isdigit():
            if len(args) <= 0:
                bot.sendMessage(chat_id, text='Nutzung: "/raid #Level"')
                return
        else:
            bot.sendMessage(chat_id, text='Bitte nur Zahlenwerte eingeben!')
            return
    else:
        bot.sendMessage(chat_id, text='Bitte nur Zahlenwerte eingeben!')
        return

    addJob(bot, update, job_queue)
    logger.info('[%s@%s] Add pokemon by rarity.' % (userName, chat_id))

    try:
        rarity = int(args[0])

        search = pref.get('search_ids')
        for x in raid_rarity[rarity]:
            if int(x) not in search:
                search.append(int(x))
        search.sort()
        pref.set('search_ids', search)
        cmd_list(bot, update)
    except Exception as e:
        logger.error('[%s@%s] %s' % (userName, chat_id, repr(e)))
        bot.sendMessage(chat_id, text='Nutzung: "/raid #Level"')


def cmd_clear(bot, update):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)

    """Removes the job if the user changed their mind"""
    logger.info('[%s@%s] Clear list.' % (userName, chat_id))

    if chat_id not in jobs:
        bot.sendMessage(chat_id, text='Du hast keinen aktiven Scanner! Bitte füge erst Pokémon zu deiner Liste hinzu mit /pokemon 1 2 3 ...')
        return

    # Remove from jobs
    job = jobs[chat_id]
    job.schedule_removal()
    del jobs[chat_id]

    # Remove from sent
    del sent[chat_id]
    # Remove from locks
    del locks[chat_id]

    pref.reset_user()

    bot.sendMessage(chat_id, text='Benachrichtigungen erfolgreich entfernt!')

def cmd_remove(bot, update, args, job_queue):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)

    logger.info('[%s@%s] Remove pokemon.' % (userName, chat_id))

    if chat_id not in jobs:
        bot.sendMessage(chat_id, text='Du hast keinen aktiven Scanner! Bitte füge erst Pokémon zu deiner Liste hinzu mit /pokemon 1 2 3 ...')
        return

    if args != []:
        if args[0].isdigit():
            if len(args) < 1 or len(args) > 2:
                bot.sendMessage(chat_id, text='Nutzung: "/lvl #minimum oder /lvl #minimum #maximum" (Ohne #!)')
                return
        else:
            bot.sendMessage(chat_id, text='Bitte nur Zahlenwerte eingeben!')
            return
    else:
        bot.sendMessage(chat_id, text='Bitte nur Zahlenwerte eingeben!')
        return

    try:
        search = pref.get('search_ids')
        for x in args:
            if int(x) in search:
                search.remove(int(x))
        pref.set('search_ids',search)
        cmd_list(bot, update)
    except Exception as e:
        logger.error('[%s@%s] %s' % (userName, chat_id, repr(e)))
        bot.sendMessage(chat_id, text='Nutzung: /entferne #Nummer (Ohne #)')

def cmd_list(bot, update):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)

    logger.info('[%s@%s] List.' % (userName, chat_id))

    if chat_id not in jobs:
        bot.sendMessage(chat_id, text='Du hast keinen aktiven Scanner! Bitte füge erst Pokémon zu deiner Liste hinzu mit /pokemon 1 2 3 ...')
        return

    try:
        lan = pref.get('language')
        tmp = 'Liste der Benachrichtigungen:\n'
        for x in pref.get('search_ids'):
            tmp += "%i %s\n" % (x, pokemon_name[lan][str(x)])
        bot.sendMessage(chat_id, text = tmp)
    except Exception as e:
        logger.error('[%s@%s] %s' % (userName, chat_id, repr(e)))
        bot.sendMessage('Liste leider Fehlerhaft. Bitte /ende eingeben und erneut beginnen')

def cmd_save(bot, update):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)

    logger.info('[%s@%s] Save.' % (userName, chat_id))

    if chat_id not in jobs:
        bot.sendMessage(chat_id, text='Du hast keinen aktiven Scanner! Bitte füge erst Pokémon zu deiner Liste hinzu mit /pokemon 1 2 3 ...')
        return
    pref.set_preferences()
    bot.sendMessage(chat_id, text='Speichern erfolgreich!')

def cmd_saveSilent(bot, update):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)

    logger.info('[%s@%s] Save.' % (userName, chat_id))

    if chat_id not in jobs:
        bot.sendMessage(chat_id, text='Du hast keinen aktiven Scanner! Bitte füge erst Pokémon zu deiner Liste hinzu mit /pokemon 1 2 3 ...')
        return
    pref.set_preferences()
    #bot.sendMessage(chat_id, text='Speichern erfolgreich!')
	
def cmd_load(bot, update, job_queue):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)

    logger.info('[%s@%s] Attempting to load.' % (userName, chat_id))
    r = pref.load()
    if r is None:
        bot.sendMessage(chat_id, text='Du hast keine gespeicherten Einstellungen!')
        return

    if not r:
        bot.sendMessage(chat_id, text='Bereits aktuell')
        return
    else:
        bot.sendMessage(chat_id, text='Laden erfolgreich!')

    # We might be the first user and above failed....
    if len(pref.get('search_ids')) > 0:
        addJob(bot, update, job_queue)
        cmd_list(bot, update)
        loc = pref.get('location')
        lat = loc[0]
        lon = loc[1]

        # Korrigiere Einstellungen, wenn jemand "null" oder "strings" hat
        if lat is None or lon is None:
            bot.sendMessage(chat_id, text='*Du hast keinen Standort gewählt! Du wirst nun nach Kiel gesetzt!*', parse_mode='Markdown')

        checkAndSetUserDefaults(pref)
			
        cmd_saveSilent(bot, update)
		
        prefmessage = "*Einstellungen:*\nMinimum IV: *%s*, Maximum IV: *%s*\nMinimum WP: *%s*, " % (miniv, maxiv, mincp) + \
        "Maximum WP: *%s*\nMinimum Level: *%s*, Maximum Level: *%s*\nModus: *%s*\nWasser: *%s*\nStandort nicht gesetzt" % (maxcp, minlvl ,maxlvl, mode, water)
        if lat is not None:
            radius = float(loc[2])*1000
            prefmessage = "*Einstellungen:*\nMinimum IV: *%s*, Maximum IV: *%s*\nMinimum WP: *%s*, " % (miniv, maxiv, mincp) + \
            "Maximum WP: *%s*\nMinimum Level: *%s*, Maximum Level: *%s*\nModus: *%s*\nWasser: *%s*\n" % (maxcp, minlvl, maxlvl, mode, water)+ \
            "Standort: %s,%s\nRadius: %s m" % (lat, lon, radius)

        bot.sendMessage(chat_id, text='%s' % (prefmessage), parse_mode='Markdown')
    else:
        if chat_id not in jobs:
            job = jobs[chat_id]
            job.schedule_removal()
            del jobs[chat_id]


def cmd_load_silent(bot, chat_id, job_queue):
    userName = ''

    pref = prefs.get(chat_id)

    logger.info('[%s@%s] Automatic load.' % (userName, chat_id))
    r = pref.load()
    if r is None:
        return

    if not r:
        return

    # We might be the first user and above failed....
    if len(pref.get('search_ids')) > 0:
        addJob_silent(bot, chat_id, job_queue)
        loc = pref.get('location')
        lat = loc[0]
        lon = loc[1]

        checkAndSetUserDefaults(pref)
			
    else:
        if chat_id not in jobs:
            job = jobs[chat_id]
            job.schedule_removal()
            del jobs[chat_id]


def cmd_location(bot, update):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)

    if chat_id not in jobs:
        bot.sendMessage(chat_id, text='Du hast keinen aktiven Scanner! Bitte füge erst Pokémon zu deiner Liste hinzu mit /pokemon 1 2 3 ...')
        return

    user_location = update.message.location
    location_radius = pref['location'][2]

    # We set the location from the users sent location.
    pref.set('location', [user_location.latitude, user_location.longitude, location_radius])

    logger.info('[%s@%s] Setting scan location to Lat %s, Lon %s, R %s' % (userName, chat_id,
        pref['location'][0], pref['location'][1], pref['location'][2]))

    # Send confirmation nessage
    bot.sendMessage(chat_id, text="Setze Standort auf: %f / %f mit Radius %.2f m" %
        (pref['location'][0], pref['location'][1], 1000*pref['location'][2]))
    addJob(bot, update, job_queue)

def cmd_location_str(bot, update, args, job_queue):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)
    location_radius = pref['location'][2]

    if chat_id not in jobs:
        bot.sendMessage(chat_id, text='Du hast keinen aktiven Scanner! Bitte füge erst Pokémon zu deiner Liste hinzu mit /pokemon 1 2 3 ...')
        return

    if len(args) <= 0:
        bot.sendMessage(chat_id, text='You have not supplied a location')
        return

    try:
        user_location = geolocator.geocode(' '.join(args), timeout=10)
        addJob(bot, update, job_queue)
    except Exception as e:
        logger.error('[%s@%s] %s' % (userName, chat_id, repr(e)))
        bot.sendMessage(chat_id, text='Standort nicht gefunden oder Openstreetmap ist down! Bitte versuche es erneut damit der Bot startet!')
        return

    # We set the location from the users sent location.
    pref.set('location', [user_location.latitude, user_location.longitude, location_radius])

    logger.info('[%s@%s] Setting scan location to Lat %s, Lon %s, R %s' % (userName, chat_id,
        pref['location'][0], pref.preferences['location'][1], pref.preferences['location'][2]))

    # Send confirmation nessage
    bot.sendMessage(chat_id, text="Setze Standort auf: %f / %f mit Radius %.2f m" %
        (pref['location'][0], pref['location'][1], 1000*pref['location'][2]))


def cmd_radius(bot, update, args):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)

    if chat_id not in jobs:
        bot.sendMessage(chat_id, text='Du hast keinen aktiven Scanner! Bitte füge erst Pokémon zu deiner Liste hinzu mit /pokemon 1 2 3 ...')
        return

    # Check if user has set a location
    user_location = pref.get('location')

    if user_location[0] is None:
        bot.sendMessage(chat_id, text="Du hast keinen Standort eingestellt. Bitte mache dies zuerst!")
        return

    # Get the users location
    logger.info('[%s@%s] Retrieved Location as Lat %s, Lon %s, R %s (Km)' % (
    userName, chat_id, user_location[0], user_location[1], user_location[2]))

    if args != []:
        if args[0].isdigit():
            if len(args) < 1:
                bot.sendMessage(chat_id, text="Aktueller Standort ist: %f / %f mit Radius %.2f m"
                                              % (user_location[0], user_location[1], user_location[2]))
        else:
            bot.sendMessage(chat_id, text='Bitte nur Zahlenwerte eingeben!')
            return
    else:
        bot.sendMessage(chat_id, text='Bitte nur Zahlenwerte eingeben!')
        return

    # Change the radius
    try:
        radius = float(args[0])
        logger.info('%s' % radius)
        pref.set('location', [user_location[0], user_location[1], radius/1000])

        logger.info('[%s@%s] Set Location as Lat %s, Lon %s, R %s (Km)' % (userName, chat_id, pref['location'][0],
            pref['location'][1], pref['location'][2]))

        # Send confirmation
        bot.sendMessage(chat_id, text="Setze Standort auf: %f / %f mit Radius %.2f m" % (pref['location'][0],
            pref['location'][1], 1000*pref['location'][2]))

    except Exception as e:
        logger.error('[%s@%s] %s' % (userName, chat_id, repr(e)))
        bot.sendMessage(chat_id, text='Radius nicht zulässig! Bitte Zahl eingeben!')
        return


def cmd_clearlocation(bot, update):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username

    pref = prefs.get(chat_id)
    pref.set('location', [None, None, None])
    bot.sendMessage(chat_id, text='Dein Standort wurde entfernt!')
    logger.info('[%s@%s] Location has been unset' % (userName, chat_id))


def cmd_unknown(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id, text="Falsche Eingabe. Ich habe dich nicht verstanden!")
	

## Functions
def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def checkAndSetUserDefaults(pref):
	
    loc = pref.get('location')
    if loc[0] is None or loc[1] is None:
        pref.set('location', [54.321362, 10.134511, 0.1])

def alarm(bot, job):
    chat_id = job.context[0]
    logger.info('[%s] Checking alarm.' % (chat_id))
    checkAndSend(bot, chat_id, prefs.get(chat_id).get('search_ids'))

def addJob(bot, update, job_queue):
    chat_id = update.message.chat_id
    userName = update.message.from_user.username
    logger.info('[%s@%s] Adding job.' % (userName, chat_id))

    try:
        if chat_id not in jobs:
            job = Job(alarm, 30, repeat=True, context=(chat_id, "Other"))
            # Add to jobs
            jobs[chat_id] = job
            job_queue.put(job)

            # User dependant
            if chat_id not in sent:
                sent[chat_id] = dict()
            if chat_id not in locks:
                locks[chat_id] = threading.Lock()
            text = "Scanner gestartet."
            bot.sendMessage(chat_id, text)
    except Exception as e:
        logger.error('[%s@%s] %s' % (userName, chat_id, repr(e)))
		
		
def addJob_silent(bot, chat_id, job_queue):
    userName = ''
    logger.info('[%s@%s] Adding job.' % (userName, chat_id))

    try:
        if chat_id not in jobs:
            job = Job(alarm, 30, repeat=True, context=(chat_id, "Other"))
            # Add to jobs
            jobs[chat_id] = job
            job_queue.put(job)

            # User dependant
            if chat_id not in sent:
                sent[chat_id] = dict()
            if chat_id not in locks:
                locks[chat_id] = threading.Lock()
            #text = "Scanner gestartet."
            #bot.sendMessage(chat_id, text)
    except Exception as e:
        logger.error('[%s@%s] %s' % (userName, chat_id, repr(e)))


def checkAndSend(bot, chat_id, pokemons):
    pref = prefs.get(chat_id)
    lock = locks[chat_id]
    logger.info('[%s] Checking pokemon and sending notifications.' % (chat_id))
    if len(pokemons) == 0:
        return

    try:

        lan = pref['language']
        mySent = sent[chat_id]
        location_data = pref['location']


        # Standort setzen wenn keiner eingegeben wurde:
        if location_data[0] is not None and location_data[2] is None:
            location_data[2] = 0.1
        if location_data[0] is None:
            location_data[0] = 54.321362
            location_data[1] = 10.134511
            location_data[2] = 0.1
        if float(location_data[2]) > 30:
            location_data[2] = 30

        # Radius + 500m für Ungenauigkeit
        radius = location_data[2] + 0.5
		
        # Berechne Koordinaten vorher
        origin = geopy.Point(location_data[0], location_data[1])
        destination_north = VincentyDistance(radius).destination(origin, 0)
        destination_east = VincentyDistance(radius).destination(origin, 90)
        destination_south = VincentyDistance(radius).destination(origin, 180)
        destination_west = VincentyDistance(radius).destination(origin, 270)

        lat_n = destination_north.latitude
        lon_e = destination_east.longitude
        lat_s = destination_south.latitude
        lon_w = destination_west.longitude

        # Hole nur noch die richtigen Pokemon aus der DB... ABER dann ist der IVFilter hinüber
        allpokes = dataSource.getRaidByIds(pokemons, lat_n, lat_s, lon_e, lon_w)

        moveNames = move_name["de"]

        lock.acquire()

        for pokemon in allpokes:
            # Prüfe ob Pokemon im Radius
            if not pokemon.filterbylocation(location_data):
                continue

            #logger.info('%s' % len(allpokes))
		
			
            encounter_id = pokemon.getGymID()
            pok_id = pokemon.getPokemonID()
            latitude = pokemon.getLatitude()
            longitude = pokemon.getLongitude()
            disappear_time = pokemon.getRaidEndTime()
            move1 = pokemon.getMove1()
            move2 = pokemon.getMove2()
            level = pokemon.getLevel()
            gym_name = pokemon.getName()
            team = pokemon.getTeam()
            team_name = ""
            if int(team) == 0:
                team_name = "Rocket"
            elif int(team) == 1:
                team_name = "Weisheit"
            elif int(team) == 2:
                team_name = "Wagemut"
            elif int(team) == 3:
                team_name = "Intuition"
			
            delta = disappear_time - datetime.utcnow()
            deltaStr = '%02dm:%02ds' % (int(delta.seconds / 60), int(delta.seconds % 60))
            disappear_time_str = disappear_time.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime("%H:%M:%S")

            pkmname =  pokemon_name[lan][pok_id]
            header = "Raidboss: " + "*" + pkmname + "*"
            info = "\nLevel: *%s*\nEnde: *%s (%s)*\nArena: *%s*\nTeam: *%s*" % (level, disappear_time_str, deltaStr, gym_name, team_name)

            move1Name = moveNames[move1]
            move2Name = moveNames[move2]
            info += "\nMoves: *%s/%s*" % (move1Name, move2Name)

            if encounter_id not in mySent:
                mySent[encounter_id] = disappear_time

                notDisappeared = delta.seconds > 0

                if notDisappeared:
                    try:
                        bot.sendLocation(chat_id, latitude, longitude)
                        bot.sendMessage(chat_id, text = '%s%s' % (header, info), parse_mode='Markdown')
                        sleep(0.5)
                    except Exception as e:
                        logger.error('[%s] %s' % (chat_id, repr(e)))

    except Exception as e:
        logger.error('[%s] %s' % (chat_id, repr(e)))
    lock.release()

    # Clean already disappeared pokemon
    current_time = datetime.utcnow() - dt.timedelta(minutes=10)
    try:

        lock.acquire()
        toDel = []
        for encounter_id in mySent:
            time = mySent[encounter_id]
            if time < current_time:
                toDel.append(encounter_id)
        for encounter_id in toDel:
            del mySent[encounter_id]
    except Exception as e:
        logger.error('[%s] %s' % (chat_id, repr(e)))
    lock.release()
    logger.info('Done.')

def read_config():
    config_path = os.path.join(
        os.path.dirname(sys.argv[0]), "config-bot.json")
    logger.info('Reading config: <%s>' % config_path)
    global config

    try:
        with open(config_path, "r", encoding='utf-8') as f:
            config = json.loads(f.read())
    except Exception as e:
        logger.error('%s' % (repr(e)))
        config = {}
    report_config()

def report_config():
    admins_list = config.get('LIST_OF_ADMINS', [])
    tmp = ''
    for admin in admins_list:
        tmp = '%s, %s' % (tmp, admin)
    tmp = tmp[2:]
    logger.info('LIST_OF_ADMINS: <%s>' % (tmp))

    logger.info('TELEGRAM_TOKEN: <%s>' % (config.get('TELEGRAM_TOKEN', None)))
    logger.info('SCANNER_NAME: <%s>' % (config.get('SCANNER_NAME', None)))
    logger.info('DB_TYPE: <%s>' % (config.get('DB_TYPE', None)))
    logger.info('DB_CONNECT: <%s>' % (config.get('DB_CONNECT', None)))
    logger.info('DEFAULT_LANG: <%s>' % (config.get('DEFAULT_LANG', None)))
    logger.info('SEND_MAP_ONLY: <%s>' % (config.get('SEND_MAP_ONLY', None)))
    logger.info('SEND_POKEMON_WITHOUT_IV: <%s>' % (config.get('SEND_POKEMON_WITHOUT_IV', None)))

    poke_ivfilter_list = config.get('POKEMON_MIN_IV_FILTER_LIST', dict())
    tmp = ''
    for poke_id in poke_ivfilter_list:
        tmp = '%s %s:%s' % (tmp, poke_id, poke_ivfilter_list[poke_id])
    tmp = tmp[1:]
    logger.info('POKEMON_MIN_IV_FILTER_LIST: <%s>' % (tmp))

def read_pokemon_names(loc):
    logger.info('Reading pokemon names. <%s>' % loc)
    config_path = "locales/pokemon." + loc + ".json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            pokemon_name[loc] = json.loads(f.read())
    except Exception as e:
        logger.error('%s' % (repr(e)))
        # Pass to ignore if some files missing.
        pass

def read_move_names(loc):
    logger.info('Reading move names. <%s>' % loc)
    config_path = "locales/moves." + loc + ".json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            move_name[loc] = json.loads(f.read())
    except Exception as e:
        logger.error('%s' % (repr(e)))
        # Pass to ignore if some files missing.
        pass

def main():
    logger.info('Starting...')
    read_config()

    # Read lang files
    path_to_local = "locales/"
    for file in os.listdir(path_to_local):
        if fnmatch.fnmatch(file, 'pokemon.*.json'):
            read_pokemon_names(file.split('.')[1])
        if fnmatch.fnmatch(file, 'moves.*.json'):
            read_move_names(file.split('.')[1])

    dbType = config.get('DB_TYPE', None)
    scannerName = config.get('SCANNER_NAME', None)

    global dataSource
    dataSource = None

    global ivAvailable

    ivAvailable = True
    dataSource = DataSources.DSPokemonGoMapIVMysql(config.get('DB_CONNECT', None))

    if not dataSource:
        raise Exception("The combination SCANNER_NAME, DB_TYPE is not available: %s,%s" % (scannerName, dbType))


    #ask it to the bot father in telegram
    token = config.get('TELEGRAM_TOKEN', None)
    updater = Updater(token)
    b = Bot(token)
    logger.info("BotName: <%s>" % (b.name))

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CommandHandler("Start", cmd_start))
    dp.add_handler(CommandHandler("help", cmd_help))
    dp.add_handler(CommandHandler("Help", cmd_help))
    dp.add_handler(CommandHandler("hilfe", cmd_help))
    dp.add_handler(CommandHandler("Hilfe", cmd_help))
    dp.add_handler(CommandHandler("add", cmd_add, pass_args = True, pass_job_queue=True))
    dp.add_handler(CommandHandler("Add", cmd_add, pass_args = True, pass_job_queue=True))
    dp.add_handler(CommandHandler("pokemon", cmd_add, pass_args = True, pass_job_queue=True))
    dp.add_handler(CommandHandler("Pokemon", cmd_add, pass_args = True, pass_job_queue=True))
    dp.add_handler(CommandHandler("raid", cmd_addByRarity, pass_args = True, pass_job_queue=True))
    dp.add_handler(CommandHandler("Raid", cmd_addByRarity, pass_args = True, pass_job_queue=True))
    dp.add_handler(CommandHandler("clear", cmd_clear))
    dp.add_handler(CommandHandler("Clear", cmd_clear))
    dp.add_handler(CommandHandler("ende", cmd_clear))
    dp.add_handler(CommandHandler("Ende", cmd_clear))
    dp.add_handler(CommandHandler("rem", cmd_remove, pass_args = True, pass_job_queue=True))
    dp.add_handler(CommandHandler("Rem", cmd_remove, pass_args = True, pass_job_queue=True))
    dp.add_handler(CommandHandler("entferne", cmd_remove, pass_args = True, pass_job_queue=True))
    dp.add_handler(CommandHandler("Entferne", cmd_remove, pass_args = True, pass_job_queue=True))
    dp.add_handler(CommandHandler("save", cmd_save))
    dp.add_handler(CommandHandler("Save", cmd_save))
    dp.add_handler(CommandHandler("speichern", cmd_save))
    dp.add_handler(CommandHandler("Speichern", cmd_save))
    dp.add_handler(CommandHandler("load", cmd_load, pass_job_queue=True))
    dp.add_handler(CommandHandler("Load", cmd_load, pass_job_queue=True))
    dp.add_handler(CommandHandler("laden", cmd_load, pass_job_queue=True))
    dp.add_handler(CommandHandler("Laden", cmd_load, pass_job_queue=True))
    dp.add_handler(CommandHandler("list", cmd_list))
    dp.add_handler(CommandHandler("List", cmd_list))
    dp.add_handler(CommandHandler("liste", cmd_list))
    dp.add_handler(CommandHandler("Liste", cmd_list))
    #dp.add_handler(CommandHandler("lang", cmd_lang, pass_args = True))
    dp.add_handler(CommandHandler("radius", cmd_radius, pass_args=True))
    dp.add_handler(CommandHandler("Radius", cmd_radius, pass_args=True))
    dp.add_handler(CommandHandler("location", cmd_location_str, pass_args=True, pass_job_queue=True))
    dp.add_handler(CommandHandler("Location", cmd_location_str, pass_args=True, pass_job_queue=True))
    dp.add_handler(CommandHandler("standort", cmd_location_str, pass_args=True, pass_job_queue=True))
    dp.add_handler(CommandHandler("Standort", cmd_location_str, pass_args=True, pass_job_queue=True))
    #dp.add_handler(CommandHandler("remloc", cmd_clearlocation))
    #dp.add_handler(CommandHandler("entfernestandort", cmd_clearlocation))
    #dp.add_handler(CommandHandler("Enfernestandort", cmd_clearlocation))
    dp.add_handler(MessageHandler([Filters.location],cmd_location))
    dp.add_handler(MessageHandler([Filters.command], cmd_unknown))

    # log all errors
    dp.add_error_handler(error)

    # add the configuration to the preferences
    prefs.add_config(config)

    # Start the Bot
    bot = b;
    updater.start_polling()
    allids = os.listdir("userdata/")
    newids = []
    for x in allids:
        newids = x.replace(".json", "")
        chat_id = int(newids)
        j = updater.job_queue
        logger.info('%s' % (chat_id))
        try:
            cmd_load_silent(b, chat_id, j)
            #bot.sendMessage(chat_id, text = 'Hinweis: Der Bot wurde neugestartet! Bitte /laden zum laden deiner Einstellungen!')

        except Exception as e:
            logger.error('%s' % (chat_id))

    logger.info('Started!')

    
    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()

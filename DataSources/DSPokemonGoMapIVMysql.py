from .DSPokemon import DSPokemon

import os
from datetime import datetime
import logging

import pymysql
import re

logger = logging.getLogger(__name__)

class DSPokemonGoMapIVMysql():
	def __init__(self, connectString):
		# open the database
		sql_pattern = 'mysql://(.*?):(.*?)@(.*?):(\d*)/(\S+)'
		(user, passw, host, port, db) = re.compile(sql_pattern).findall(connectString)[0]
		self.__user = user
		self.__passw = passw
		self.__host = host
		self.__port = int(port)
		self.__db = db
		logger.info('Connecting to remote database')
		self.__connect()

	def getRaidByIds(self, ids, lat_n, lat_s, lon_e, lon_w):
		pokelist = []
		
		sqlquery = ("SELECT r.gym_id, r.pokemon_id, g.latitude, g.longitude, r.level, "
			"r.battle, r.end, r.move_1, r.move_2, d.name, g.team_id "
			"FROM raid r, gym g, gymdetails d WHERE r.gym_id = g.gym_id AND r.gym_id = d.gym_id AND r.end > UTC_TIMESTAMP()")
		sqlquery += ' AND r.pokemon_id in ('
		for pokemon in ids:
			sqlquery += str(pokemon) + ','
		sqlquery = sqlquery[:-1]
		sqlquery += ')'
		sqlquery += ' AND g.latitude BETWEEN "' + str(lat_s) + '" AND "' + str(lat_n) + '" AND g.longitude BETWEEN "' + str(lon_w) + '" AND "' + str(lon_e) +'"'
		sqlquery += ' ORDER BY r.level DESC'

		try:
			with self.con:
				cur = self.con.cursor()

				cur.execute(sqlquery)
				rows = cur.fetchall()
				for row in rows:
					gym_id = str(row[0])
					pok_id = str(row[1])
					latitude = str(row[2])
					longitude = str(row[3])
					level = str(row[4])

					raid_start = str(row[5])
					raid_start_time = datetime.strptime(raid_start[0:19], "%Y-%m-%d %H:%M:%S")
					raid_end = str(row[6])
					raid_end_time = datetime.strptime(raid_end[0:19], "%Y-%m-%d %H:%M:%S")			

					move1 = str(row[7])
					move2 = str(row[8])
					name = str(row[9])
					team = str(row[10])

					poke = DSPokemon(gym_id, pok_id, latitude, longitude, raid_start_time, raid_end_time, move1, move2, level, name, team)
					pokelist.append(poke)
		except pymysql.err.OperationalError as e:
			if e.args[0] == 2006:
				self.__reconnect()
			else:
				logger.error(e)
		except Exception as e:
			logger.error(e)

		return pokelist

		
	def __connect(self):
		self.con = pymysql.connect(user=self.__user,password=self.__passw,host=self.__host,port=self.__port,database=self.__db)

	def __reconnect(self):
		logger.info('Reconnecting to remote database')
		self.__connect()

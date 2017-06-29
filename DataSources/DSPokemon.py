from geopy.distance import great_circle
import matplotlib.path as mplPath
import numpy as np

class DSPokemon:
	def __init__(self, gym_id, pokemon_id, latitude, longitude, raid_start_time, raid_end_time, move1, move2, level, name, team):
		self.gym_id = gym_id
		self.pokemon_id = pokemon_id
		self.latitude = latitude
		self.longitude = longitude
		self.raid_start_time = raid_start_time # Should be datetime
		self.raid_end_time = raid_end_time
		self.move1 = move1
		self.move2 = move2
		self.level = level
		self.name = name
		self.team = team

	def getGymID(self):
		return self.gym_id

	def getPokemonID(self):
		return self.pokemon_id

	def getLatitude(self):
		return self.latitude

	def getLongitude(self):
		return self.longitude

	def getRaidStartTime(self):
		return self.raid_start_time

	def getRaidEndTime(self):
		return self.raid_end_time

	def getMove1(self):
		return self.move1

	def getMove2(self):
		return self.move2

	def getLevel(self):
		return self.level

	def getName(self):
		return self.name

	def getTeam(self):
		return self.team

	def filterbylocation(self,user_location):
		user_lat_lon = (user_location[0], user_location[1])
		pok_loc = (float(self.latitude), float(self.longitude))
		return great_circle(user_lat_lon, pok_loc).km <= user_location[2]
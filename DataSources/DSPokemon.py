from geopy.distance import great_circle
import matplotlib.path as mplPath
import numpy as np

class DSPokemon:
	def __init__(self, encounter_id, spawnpoint_id, pokemon_id, latitude, longitude, disappear_time, ivs, iv_attack, iv_defense, iv_stamina, move1, move2, cp, cp_multiplier):
		self.encounter_id = encounter_id
		self.spawnpoint_id = spawnpoint_id
		self.pokemon_id = pokemon_id
		self.latitude = latitude
		self.longitude = longitude
		self.disappear_time = disappear_time # Should be datetime
		self.ivs = ivs
		self.iv_attack = iv_attack
		self.iv_defense = iv_defense
		self.iv_stamina = iv_stamina
		self.move1 = move1
		self.move2 = move2
		self.cp = cp
		self.cp_multiplier = cp_multiplier

	def getEncounterID(self):
		return self.encounter_id

	def getSpawnpointID(self):
		return self.spawnpoint_id

	def getPokemonID(self):
		return self.pokemon_id

	def getLatitude(self):
		return self.latitude

	def getLongitude(self):
		return self.longitude

	def getDisappearTime(self):
		return self.disappear_time

	def getIVs(self):
		return self.ivs

	def getIVattack(self):
		return self.iv_attack
    
	def getIVdefense(self):
		return self.iv_defense
        
	def getIVstamina(self):
		return self.iv_stamina
        
	def getMove1(self):
		return self.move1

	def getMove2(self):
		return self.move2
		
	def getCP(self):
		return self.cp

	def getCPM(self):
		return self.cp_multiplier

	def filterbylocation(self,user_location):
		user_lat_lon = (user_location[0], user_location[1])
		pok_loc = (float(self.latitude), float(self.longitude))
		return great_circle(user_lat_lon, pok_loc).km <= user_location[2]

	# Filter für die Kieler Förde (Polygon)
	def filterbywater(self, lat, lon):
		bbPath = mplPath.Path(
					np.array(
					  [ [54.315957494664644,10.135703086853027],
                        [54.317722294925154,10.137312412261963],
                        [54.32037561081846,10.142827033996582],
                        [54.32225285373755,10.144929885864258],
                        [54.325706756894654,10.147483348846436],
                        [54.32833453317978,10.148792266845703],
                        [54.332563647886225,10.153577327728271],
                        [54.33552877367003,10.157396793365479],
                        [54.33780564495387,10.159327983856201],
                        [54.34122071547086,10.15859842300415],
                        [54.34129576877982,10.157310962677002],
                        [54.34446039193442,10.155787467956543],
                        [54.34483562753454,10.156645774841309],
                        [54.3448481353289,10.155057907104492],
                        [54.34621146209445,10.153684616088867],
                        [54.34686184058242,10.15510082244873],
                        [54.34744967382251,10.154070854187012],
                        [54.34696189789789,10.1523756980896],
                        [54.35078890736667,10.14538049697876],
                        [54.35158928258557,10.146431922912598],
                        [54.352764805426204,10.144178867340088],
                        [54.352152037077545,10.14310598373413],
                        [54.35331503860571,10.141797065734863],
                        [54.3575415841593,10.143449306488037],
                        [54.363117958225644,10.148148536682129],
                        [54.362367817440415,10.151731967926025],
                        [54.36309295375351,10.153448581695557],
                        [54.36505326490111,10.149521827697754],
                        [54.3681035525692,10.150680541992188],
                        [54.36835356610299,10.155658721923828],
                        [54.37517834763587,10.161237716674805],
                        [54.3777029793626,10.168447494506836],
                        [54.38130218584361,10.170679092407227],
                        [54.38402637535947,10.169477462768555],
                        [54.38720020298442,10.177931785583496],
                        [54.388449674083965,10.176386833190918],
                        [54.38897444060165,10.191149711608887],
                        [54.39084855195669,10.196428298950195],
                        [54.39164814675107,10.191707611083984],
                        [54.39746972659664,10.190420150756836],
                        [54.40029277045167,10.193681716918945],
                        [54.40441456518904,10.193853378295898],
                        [54.41355597698857,10.188360214233398],
                        [54.417551582442094,10.182008743286133],
                        [54.4241185127849,10.177030563354492],
                        [54.42710949549051,10.17333984375],
                        [54.4280082434376,10.173683166503906],
                        [54.433000928648156,10.171537399291992],
                        [54.43320062340274,10.169477462768555],
                        [54.434798146398855,10.169992446899414],
                        [54.434997832393336,10.174369812011719],
                        [54.441237529265166,10.18157958984375],
                        [54.446827490342116,10.185012817382812],
                        [54.44782561738731,10.192995071411133],
                        [54.449961542142056,10.198745727539062],
                        [54.45764590461183,10.202178955078125],
                        [54.48033139174732,10.250244140625],
                        [54.43722436767486,10.30517578125],
                        [54.4346883333125,10.304832458496094],
                        [54.42450302960203,10.278568267822266],
                        [54.41970906941397,10.273418426513672],
                        [54.4169123336864,10.235481262207031],
                        [54.41427522202616,10.223894119262695],
                        [54.411927663403546,10.224409103393555],
                        [54.404784264762185,10.214624404907227],
                        [54.39933846078872,10.208616256713867],
                        [54.39399187653719,10.207757949829102],
                        [54.39354213207331,10.205183029174805],
                        [54.3912433611543,10.207586288452148],
                        [54.38699529341434,10.206127166748047],
                        [54.38079732350767,10.198745727539062],
                        [54.380147482134326,10.19308090209961],
                        [54.377747978714176,10.19308090209961],
                        [54.37199859788175,10.193595886230469],
                        [54.3670984901305,10.195140838623047],
                        [54.36599838557798,10.194711685180664],
                        [54.363298004016194,10.181236267089844],
                        [54.36169769412802,10.177116394042969],
                        [54.357496584030955,10.178489685058594],
                        [54.354995719281355,10.176429748535156],
                        [54.3538952905661,10.175399780273438],
                        [54.35089397154768,10.175914764404297],
                        [54.34849275849608,10.17308235168457],
                        [54.344990737962156,10.172996520996094],
                        [54.33898657994307,10.174026489257812],
                        [54.33568391921672,10.165786743164062],
                        [54.331580243893605,10.171451568603516],
                        [54.33047918815351,10.17359733581543],
                        [54.323321607256034,10.155916213989258],
                        [54.32517368819471,10.154199600219727],
                        [54.32437279856275,10.150079727172852],
                        [54.3220200950865,10.150508880615234],
                        [54.3221202128692,10.148792266845703],
                        [54.318515819185606,10.143814086914062],
                        [54.31901644830349,10.142440795898438]
                                   ]))

		return bbPath.contains_point((float(lat), float(lon)))
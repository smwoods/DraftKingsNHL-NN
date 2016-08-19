import requests
import json
import time
import random
from pymongo import MongoClient

client = MongoClient()
db = client.nhl

for season in range(2009, 2010):

	# Build season string ID
	season_id = str(season) + str(season + 1)

	print('Getting skaters from ' + season_id)
	# Build URL to get all skaters from this season
	skater_summary_url = 'http://www.nhl.com/stats/rest/grouped/skaters/season/skatersummary?cayenneExp=seasonId=' + season_id + '%20and%20gameTypeId=2'
	
	# Add each skater to the database as a skater document
	r = requests.get(url=skater_summary_url)
	skaters = json.loads(r.content.decode("utf-8"))['data']
	for skater in skaters:
		if db.skaters.find({'playerId': skater['playerId']}).count() == 0:
			db.skaters.insert_one(skater)

	print('Starting game logs...')

	# For each skater, add all his game logs to the database
	count = 1
	for skater in skaters:
		print(str(count) + ' out of ' + str(len(skaters)))

		# Build URL for this skaters game logs
		skater_game_log_url = 'https://statsapi.web.nhl.com/api/v1/people/' + str(skater['playerId']) + '/stats?stats=gameLog&expand=stats.team&season=' + season_id + '&site=en_nhl'
		r = requests.get(url=skater_game_log_url)

		games = json.loads(r.content.decode("utf-8"))['stats'][0]['splits']
		for game in games:

			# Make sure we're not inserting a duplicate, and if not add game log to database
			if db.skater_games.find({ 'playerId': skater['playerId'], 'date': game['date'] }).count() == 0:
				game['playerId'] = skater['playerId']
				db.skater_games.insert_one(game)
			else:
				print('Player ' + str(skater['playerId']) + ' game on ' + str(game['date']) + ' already in DB')

			
		count += 1
		# Put scraper to sleep, as a courtesy to nhl.com
		time.sleep(random.randint(3, 4))

# Create index so players can be looked up quickly by their ID
db.skater_games.create_index('playerId')

print('Done!')


		

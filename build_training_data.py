from pymongo import MongoClient
import csv


# Open connection to mongoDB
client = MongoClient()
db = client.nhl

# Create and open csv file to output data
output = open('training_data.csv', 'w')
wr = csv.writer(output, quoting=csv.QUOTE_NONE)

# Get a list of all players in the database by their IDs
all_skaters = db.skaters.find({ }, { 'playerId': 1, '_id': 0 })
all_skaters_ids = [x['playerId'] for x in all_skaters]

count = 1
for player_id in all_skaters_ids:
	print('Player ' + str(count) + ' out of ' + str(len(all_skaters_ids)))

	# Find all games played by this skater
	active_seasons = db.skater_games.find({ 'playerId': player_id }).distinct('season')
	
	for season in active_seasons:

		# Get all games the player played this season in chronological order
		games_this_season = db.skater_games.find({ 'playerId': player_id, 'season': season }).sort('date')
		
		# Only process seasons where the player has played more than 5 games
		if games_this_season.count() < 10:
			continue

		goals, assists, shots, blocked, shp, sh_toi, even_toi, pp_toi  = [], [], [], [], [], [], [], []

		# Function to convert playing time string values to integer second values (eg. '10:05' -> 605)
		time_to_secs = lambda x:  60 * int(x.split(':')[0]) + int(x.split(':')[1])

		# Collect relevant stats into lists
		for game in games_this_season:

			stats = game['stat']

			goals.append(stats['goals'])
			assists.append(stats['assists'])
			shots.append(stats['shots'])
			blocked.append(stats['blocked'])
			shp.append(stats['shortHandedPoints'])
			sh_toi.append(time_to_secs(stats['shortHandedTimeOnIce']))
			even_toi.append(time_to_secs(stats['evenTimeOnIce']))
			pp_toi.append(time_to_secs(stats['powerPlayTimeOnIce']))
			
		game_tups = [x for x in zip(goals, assists, shots, blocked, shp, sh_toi, even_toi, pp_toi)]
		
		for i in range(9, len(game_tups)-1):

			#Get running average for last game, last 5 games, and entire season
			last1 = list(game_tups[i])
			last5 = [round(sum(x) / float(5), 3) for x in zip(*game_tups[i-4: i+1])]
			whole_season = [round(sum(x) / float(len(game_tups[:i+1])), 3) for x in zip(*game_tups[:i+1])]

			outrow = []
			for j in range(len(last1)):
				outrow.append(last1[j])
				outrow.append(last5[j])
				outrow.append(whole_season[j])
			
			# Scoring system: 3 pts per goal, 2 pts per assist, 0.5 pts per shot, 
			# 0.5 pts per blocked shot, 1 pt per shorthanded goal, 1.5 pts per hat trick
			score_game = lambda x: (3*x[0]) + (2*x[1]) + (0.5*x[2]) + (0.5*x[3]) + (1*x[4]) + (1.5*(x[0]//3))

			# Score their NEXT game (the one you would be making a prediction on)
			outrow.append(score_game(game_tups[i+1]))

			wr.writerow(outrow)
	count += 1


from keras.models import load_model
from pymongo import MongoClient
import numpy
from scipy import stats

# Open connection to mongoDB
client = MongoClient()
db = client.nhl

skater_ids =  [int(line.rstrip('\n')) for line in open('skater_ids.txt')]
season = '20152016'


print('Creating input rows from data...')
prediction_input = []
for skater_id in skater_ids:

	# Build a single row for this skater based on their most recent games

	games_this_season = db.skater_games.find({ 'playerId': skater_id, 'season': season }).sort([('date', -1)])
		
	# Only process seasons where the player has played more than 5 games
	if games_this_season.count() < 10:
		outfile.write(str(skater_id) + ' ' + str(0) + '\n')
		continue

	goals, assists, shots, blocked, shp, sh_toi, even_toi, pp_toi  = [], [], [], [], [], [], [], []

	# Function to convert playing time string values to integer second values (eg. '10:05' -> 605)
	time_to_secs = lambda x:  60 * int(x.split(':')[0]) + int(x.split(':')[1])

	for game in games_this_season:

		stat = game['stat']

		goals.append(stat['goals'])
		assists.append(stat['assists'])
		shots.append(stat['shots'])
		blocked.append(stat['blocked'])
		shp.append(stat['shortHandedPoints'])
		sh_toi.append(time_to_secs(stat['shortHandedTimeOnIce']))
		even_toi.append(time_to_secs(stat['evenTimeOnIce']))
		pp_toi.append(time_to_secs(stat['powerPlayTimeOnIce']))
		
	game_tups = [x for x in zip(goals, assists, shots, blocked, shp, sh_toi, even_toi, pp_toi)]
	
	last1 = list(game_tups[0])
	last5 = [round(sum(x) / float(5), 3) for x in zip(*game_tups[:5])]
	whole_season = [round(sum(x) / float(len(game_tups)), 3) for x in zip(*game_tups)]

	outrow = []
	for j in range(len(last1)):
		outrow.append(last1[j])
		outrow.append(last5[j])
		outrow.append(whole_season[j])

	prediction_input.append(outrow)
	
# Combine the newly generated rows with the training data to be normalized
print('Normalizing input data...')
prediction_input = numpy.array(prediction_input)
dataset = numpy.loadtxt('training_data_shuf.csv', delimiter=",")
X = numpy.append(dataset[:,0:-1], prediction_input, axis=0)
X = stats.zscore(X)
norm_prediction_input = X[-len(prediction_input):]

# Create predictions for the new rows
print('Creating predictions...')
model = load_model('nhl_model.h5')
predictions = model.predict(norm_prediction_input)
predictions = [float(x[0]) for x in predictions]

# Sort and write to output file
print('Writing output...')
outfile = open('skater_predictions.txt', 'w')
sorted_predictions = sorted(list(zip(skater_ids, predictions)), key=lambda x: x[1], reverse=True)
for p in sorted_predictions:
	name = db.skaters.find_one( { 'playerId': p[0] }, { 'playerName': 1 } )['playerName']
	outfile.write(name + ' ' + str(p[1]) + '\n')


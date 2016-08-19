from keras.models import Sequential, load_model
from keras.layers import Dense, Activation
import numpy
from scipy import stats

# Fix random seed for reproducibility
seed = 7
numpy.random.seed(seed)


# Load nhl dataset
dataset = numpy.loadtxt('training_data_shuf.csv', delimiter=",")

# Split into input (X) and output (Y) variables
X = dataset[:,0:-1]
Y = dataset[:,-1]

# Normalize input data
X = stats.zscore(X)

# Divide data into training and test (80% training, 20% test)
cutoff = int(0.8 * len(X))
X_train, Y_train = X[:cutoff], Y[:cutoff]
X_test, Y_test = X[cutoff:], Y[cutoff:]

# Build feed-forward neural network architecture
model = Sequential()
model.add(Dense(input_dim=len(X[0]), output_dim=24))
model.add(Activation('relu'))
model.add(Dense(input_dim=24, output_dim=24))
model.add(Activation('relu'))
model.add(Dense(input_dim=24, output_dim=12))
model.add(Activation('relu'))
model.add(Dense(input_dim=12, output_dim=1))
model.add(Activation('linear'))
model.compile(loss='mean_absolute_error', optimizer='rmsprop')

# Fit the model
model.fit(X_train, Y_train, nb_epoch=10, batch_size=32)

# Save the model so it can be loaded in other files easily
model.save('nhl_model.h5')

# Make predictions on the test data
predictions = model.predict(X_test, batch_size=32)

# Create tuples of predicted vs actual, for comparison
comparison = list(zip([x[0] for x in predictions], Y_test))

print('Some random predictions')
for x in comparison[:50]: print(x)
print()

# Find the players with the highest predicted values, and the highest actual values
top_predictions = sorted(comparison, key=lambda x: x[0])[-1000:][::-1]
top_scorers = sorted(comparison, key=lambda x: x[1])[-1000:][::-1]

print('Highest predicted')
for x in top_predictions[:50]: print(x)
print()
print('Actual highest')
for x in top_scorers[:50]: print(x)
print()

# Scoring function
predicted_score = sum([x[1] for x in top_predictions])
available_score = sum([x[1] for x in top_scorers])
print('Top 1000:')
print('Predicted score: ' + str(predicted_score))
print('Available score: ' + str(available_score))
print('Score: ' + str(predicted_score / float(available_score)))





from sklearn.preprocessing import MinMaxScaler
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM
from tensorflow.keras.optimizers import Adam

keras_data = draw_result.iloc[:, 2:8].astype(int)

# Normalize the data
scaler = MinMaxScaler(feature_range=(0, 1))
keras_data_normalized = scaler.fit_transform(keras_data)

# Update data loading and splitting functions
def _load_data(df, n_prev=30):
    docX, docY = [], []
    for i in range(len(df) - n_prev):
        docX.append(df[i:i + n_prev])
        docY.append(df[i + n_prev])
    alsX = np.array(docX)
    alsY = np.array(docY)
    return alsX, alsY

def train_test_split(df, test_size=0.2):
    num_train = round(len(df) * (1 - test_size))
    X_train, y_train = _load_data(df[:num_train])
    X_test, y_test = _load_data(df[num_train:])
    return X_train, y_train, X_test, y_test

# Split the normalized data
print(keras_data_normalized)
X_train, y_train, X_test, y_test = train_test_split(keras_data_normalized)

# Define the improved model
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
model.add(Dropout(0.2))
model.add(LSTM(50, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(25, activation="relu"))
model.add(Dense(y_train.shape[1]))  # Ensure output shape matches target shape

# Compile the model
model.compile(optimizer=Adam(learning_rate=0.001), loss="mae", metrics=["mse"])

# Train the model
hist = model.fit(
    X_train, y_train, 
    validation_split=0.1, 
    epochs=50, 
    batch_size=64, 
    verbose=1
)

# Evaluate on the test set
test_loss, test_mse = model.evaluate(X_test, y_test, verbose=1)
print(f"Test Loss: {test_loss}, Test MSE: {test_mse}")

# Inverse transform predictions to original scale (optional)
predicted = model.predict(X_test)
predicted_original_scale = scaler.inverse_transform(predicted)
rmse = np.sqrt(((predicted_original_scale - y_test) ** 2).mean(axis=0))
print(f"\nPredicted numbers: {np.around(rmse)}")

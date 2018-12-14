import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xgboost
import lightgbm
import math
from scipy.stats import pearsonr
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import explained_variance_score
from sklearn.model_selection import KFold
from sklearn import preprocessing
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.linear_model import Lasso
from sklearn.model_selection import KFold, cross_val_score, train_test_split

def perf(actual, pred):
    total = 0
    for i in range(len(actual)):
        total += abs(actual[i] - pred[i]) / actual[i]
    return 1 - total/len(actual)

def perf1(est, X, y):
    est.fit(X, y)
    pred = est.predict(X)
    total = 0
    for i in range(len(y)):
        total += abs(y[i] - pred[i]) / y[i]
    return 1 - total/len(y)

def perf_score(model, X, y, n_folds=5):
    kf = KFold(n_folds, shuffle=True, random_state=1000).get_n_splits(X)
    return cross_val_score(model, X, y, scoring=perf1, cv = kf)def rmsle_cv(model, X, y, n_folds=5):

# Read the data into a data frame
data = pd.read_csv('data_train.csv', parse_dates=[0,18])
features = data.iloc[:,:23].columns.tolist()
# Check the number of data points in the data set
print(len(data))
# Check the number of features in the data set
print(len(data.columns))
# Check the data types
print(data.dtypes.unique())

data.select_dtypes(include=['O']).columns.tolist()

# Check any number of columns with NaN
print(data.isnull().any().sum(), ' / ', len(data.columns))
# Check any number of data points with NaN
print(data.isnull().any(axis=1).sum(), ' / ', len(data))

# Drop the 'builder_id' column and also date features
data = data.drop(['builder_id'],axis=1)
# Now let's check our data statistics

# Check any number of columns with NaN
print(data.isnull().any().sum(), ' / ', len(data.columns))
# Check any number of data points with NaN
print(data.isnull().any(axis=1).sum(), ' / ', len(data), end=" -> ")
print(data.isnull().any(axis=1).sum() / len(data), "%")

# Calculate age
data["age"] = 2018 - data["built_year"]
data.drop(["built_year"], axis=1, inplace=True)
cols = data.columns.tolist()
cols = cols[-1:] + cols[:-1]
data = data[cols]
# Count days since apartment was constructed --------------------------------------------------------------
data["day_diff"] = -(data["construnction_completion_date"] - data["contract_date"]).dt.days
data.drop(["contract_date"], axis=1, inplace=True)
data.drop(["construnction_completion_date"], axis=1, inplace=True)
cols = data.columns.tolist()
cols = cols[-1:] + cols[:-1]
data = data[cols]

# Change label ---------------------------------------------------------------------------------------------
lb = preprocessing.LabelBinarizer()
# 1st_class_reg, try to categorize id of 1st_class into six id (see test_data)
temp = lb.fit_transform(data["first_class_region_id"].values.reshape(-1, 1))
data.drop(["first_class_region_id"], axis=1, inplace=True)
temp = temp[:, :5]
data = pd.concat([data, pd.DataFrame(temp, columns=["one", "two", "three", "four", "five"])], axis=1)
data.fillna(0,inplace=True)
cols = data.columns.tolist()
cols = cols[-5:] + cols[:-5]
data = data[cols]

features = data.iloc[:,:25].columns.tolist()
print(features)
target = data.iloc[:,25].name
print(target)

# CHECK correlation of each column
correlations = {}
for f in features:
    data_temp = data[[f,target]]
    x1 = data_temp[f].values
    x2 = data_temp[target].values
    key = f + ' vs ' + target
    correlations[key] = pearsonr(x1,x2)[0]

data_correlations = pd.DataFrame(correlations, index=['Value']).T
data_correlations.loc[data_correlations['Value'].abs().sort_values(ascending=False).index]

new_data = data[['floor', 'area', 'area_of_parking_lot',
                 'number_of_cars_in_parking_lot', 'external_vehicle_entrance', 'avg_management_fee',
                 'number_of_households', 'avg_age_of_residents']]

X = new_data.values
y = data.price.values


lasso = make_pipeline(RobustScaler(), Lasso(alpha =0.0005, random_state=1))
model_xgb = xgboost.XGBRegressor(n_estimators=25, learning_rate=0.15, gamma=0, subsample=0.75,
                       colsample_bytree=1, max_depth=10)
model_lgb = lightgbm.LGBMRegressor(objective='regression',num_leaves=5,
                              learning_rate=0.05, n_estimators=720,
                              bagging_freq = 5, feature_fraction = 0.25)

score = perf_score(model_xgb, X, y)
print("Xgboost score: {:.4f} ({:.4f})\n".format(score.mean(), score.std()))
score = perf_score(lasso, X, y)
print("Lasso score: {:.4f} ({:.4f})\n".format(score.mean(), score.std()))
score = perf_score(model_lgb, X, y)
print("Lasso score: {:.4f} ({:.4f})\n".format(score.mean(), score.std()))
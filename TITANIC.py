import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedShuffleSplit, GridSearchCV

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

titanic_df = pd.read_csv(r"C:\Users\DELL\Downloads\Titanic-Dataset.csv")

split = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
for train_indices, test_indices in split.split(titanic_df, titanic_df[["Survived", "Pclass", "Sex"]]):
    strat_train_set = titanic_df.loc[train_indices]
    strat_test_set = titanic_df.loc[test_indices]


class AgeImputer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        imputer = SimpleImputer(strategy="mean")
        X['Age'] = imputer.fit_transform(X[['Age']])
        return X


class FeatureEncoder(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        encoder = OneHotEncoder(sparse_output=False)
        embarked_encoded = encoder.fit_transform(X[['Embarked']])
        sex_encoded = encoder.fit_transform(X[['Sex']])

        embarked_cols = encoder.categories_[0]
        sex_cols = encoder.categories_[0]
        for i, col in enumerate(embarked_cols):
            X[col] = embarked_encoded[:, i]
        for i, col in enumerate(sex_cols):
            X[col] = sex_encoded[:, i]
        return X

class FeatureDropper(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.drop(["Embarked", "Name", "Ticket", "Cabin", "Sex"], axis=1, errors="ignore")

from sklearn.pipeline import Pipeline

pipeline = Pipeline([
    ("ageimputer", AgeImputer()),
    ("featureencoder", FeatureEncoder()),
    ("featuredropper", FeatureDropper())
])

strat_train_set = pipeline.fit_transform(strat_train_set)
strat_test_set = pipeline.transform(strat_test_set)

X_train = strat_train_set.drop(['Survived'], axis=1)
y_train = strat_train_set['Survived']
X_test = strat_test_set.drop(['Survived'], axis=1)
y_test = strat_test_set['Survived']

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

param_grid = {
    "n_estimators": [10, 100, 200, 500],
    "max_depth": [None, 5, 10],
    "min_samples_split": [2, 3, 4]
}
grid_search = GridSearchCV(RandomForestClassifier(), param_grid, cv=3, scoring="accuracy", return_train_score=True)
grid_search.fit(X_train_scaled, y_train)

final_clf = grid_search.best_estimator_
print(final_clf)

test_score = final_clf.score(X_test_scaled, y_test)
print("Test Accuracy:", test_score)

cv_results = pd.DataFrame(grid_search.cv_results_)
plt.figure(figsize=(10, 6))
sns.barplot(x='param_n_estimators', y='mean_test_score', hue='param_max_depth', data=cv_results, palette='viridis',
            dodge=True, width=0.5)
plt.title('Cross-Validation Accuracy for Different Hyperparameter Combinations')
plt.xlabel('Number of Estimators')
plt.ylabel('Mean Test Score')
plt.legend(title='Max Depth')
plt.show()

final_data = pipeline.fit_transform(titanic_df)
X_final = final_data.drop(['Survived'], axis=1)
y_final = final_data['Survived']
X_final_scaled = scaler.fit_transform(X_final)

prod_clf = RandomForestClassifier()
grid_search.fit(X_final_scaled, y_final)
prod_final_clf = grid_search.best_estimator_

titanic_test_data = pd.read_csv(r'C:\Users\DELL\Downloads\test.csv')
final_test_data = pipeline.fit_transform(titanic_test_data)

X_final_test = final_test_data
X_final_test = X_final_test.ffill()

scaler = StandardScaler()
X_data_final_test = scaler.fit_transform(X_final_test)

predictions = prod_final_clf.predict(X_data_final_test)
print(predictions)

final_df = pd.DataFrame({'PassengerId': titanic_test_data['PassengerId'], 'Survived': predictions})
final_df.to_csv(r"C:\Users\DELL\Downloads\predictions.csv", index=False)




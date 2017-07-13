#!/usr/bin/python

import sys
import pickle
sys.path.append("../tools/")

from feature_format import featureFormat, targetFeatureSplit
from tester import dump_classifier_and_data
from sklearn.feature_selection import SelectKBest, f_classif
from enronfunc import computeFraction,get_best_features,eval_clf,missing_values,plotFeature
from sklearn import preprocessing
import numpy
from sklearn.grid_search import GridSearchCV



### Select what features you'll use.
### features_list is a list of strings, each of which is a feature name.
### The first feature must be "poi".
features_list = ['poi',
                 'salary',
                 #'email_address', 
                 #'from_messages',
                 #'from_poi_to_this_person',
                 #'from_this_person_to_poi',
                 'shared_receipt_with_poi',
                 #'to_messages',
                 'bonus',
                 'deferral_payments',
                 'deferred_income',
                 'director_fees',
                 'exercised_stock_options',
                 'expenses',
                 'loan_advances',
                 'long_term_incentive',
                 'other',
                 'restricted_stock',
                 'restricted_stock_deferred',
                 'total_payments',
                 'total_stock_value'] 

### Load the dictionary containing the dataset
with open("final_project_dataset.pkl", "r") as data_file:
    data_dict = pickle.load(data_file)

###Data Exploration
###Total data points in the dataset
print('Total number of data points: %d' % len(data_dict.keys()))

###number of POI and non POI
num_poi = 0
for name in data_dict.keys():
    if data_dict[name]['poi'] == True:
        num_poi += 1
print('Number of Persons of Interest: %d' % num_poi)
print('Number of people without Person of Interest label: %d' % (len(data_dict.keys()) - num_poi))

###Number of features
print('Total number of features: %d' % len(data_dict.values()[1]))

###Features with missing values
all_features = (data_dict.values()[1]).keys()
missing_features = missing_values(data_dict,all_features)
print missing_features

###Remove outliers
#plotFeature(data_dict,'salary','bonus')
data_dict.pop('TOTAL',0)
data_dict.pop('THE TRAVEL AGENCY IN THE PARK',0)
#print('Total number of data points: %d' % len(data_dict.keys()))

### Create new feature(s)
for name in data_dict:

	data_point = data_dict[name]
	from_poi_to_this_person = data_point["from_poi_to_this_person"]
	to_messages = data_point["to_messages"]
	fraction_from_poi = computeFraction( from_poi_to_this_person, to_messages )

	from_this_person_to_poi = data_point["from_this_person_to_poi"]
	from_messages = data_point["from_messages"]
	fraction_to_poi = computeFraction( from_this_person_to_poi, from_messages )

	data_point["fraction_from_poi"] = fraction_from_poi
	data_point["fraction_to_poi"] = fraction_to_poi

features_list += ['fraction_from_poi','fraction_to_poi']

#print features_list

###select best features using k best
best_features = get_best_features(data_dict, features_list, 6)
print best_features

### Store to my_dataset for easy export below.
my_dataset = data_dict

### Extract features and labels from dataset for local testing
data = featureFormat(my_dataset, best_features, sort_keys = True)
labels, features = targetFeatureSplit(data)

#scale the features
scaler = preprocessing.MinMaxScaler()
features = scaler.fit_transform(features)

###Try a varity of classifiers
from sklearn.naive_bayes import GaussianNB
g_clf = GaussianNB()
print "GaussianNB"
eval_clf(g_clf, features, labels)


from sklearn import tree
t_clf = tree.DecisionTreeClassifier(splitter = "random")
print "Decision tree"
eval_clf(t_clf, features, labels)


from sklearn.svm import SVC
s_clf = SVC(kernel='linear', C=500,gamma = 0.001)
print "SVM"
eval_clf(s_clf, features, labels)

from sklearn.cluster import KMeans
k_clf = KMeans(n_clusters=2,tol=0.001)
print "KMeans"
eval_clf(k_clf, features, labels)


#from sklearn.ensemble import RandomForestClassifier
#rf_clf = RandomForestClassifier(n_estimators = 10,random_state = 50)
#print "Random Forrest"
#eval_clf(rf_clf, features, labels)

clf = g_clf

### Task 6: Dump your classifier, dataset, and features_list so anyone can
### check your results. You do not need to change anything below, but make sure
### that the version of poi_id.py that you submit can be run on its own and
### generates the necessary .pkl files for validating your results.

dump_classifier_and_data(clf, my_dataset, best_features)
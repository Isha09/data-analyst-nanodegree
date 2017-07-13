import pickle
import sys
from sklearn.feature_selection import SelectKBest, f_classif
from feature_format import featureFormat, targetFeatureSplit
from numpy import mean
from sklearn import cross_validation
import matplotlib.pyplot as plt
sys.path.append("../tools/")
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score,classification_report,confusion_matrix



###find number of missing values in all features
def missing_values(data, featurelist):
    missing_val = {}
    for feature in featurelist:
        missing_val[feature] = 0
    for key in data.keys():
        for ftr in featurelist:
            if data[key][ftr] == 'NaN':
                missing_val[ftr] += 1
    return missing_val


###visulaize features
def plotFeature(data_dict, fx, fy):
    """ Plot with flag = True in Red """
    data = featureFormat(data_dict, [fx, fy, 'poi'])
    for point in data:
        x = point[0]
        y = point[1]
        poi = point[2]
        if poi:
            color = 'red'
        else:
            color = 'blue'
        plt.scatter(x, y, color=color)
    plt.xlabel(fx)
    plt.ylabel(fy)
    plt.show()


###identify best k features out of features list
def get_best_features(dataset, feature_set, knum):
    data = featureFormat(dataset, feature_set, sort_keys = True)
    labels, features = targetFeatureSplit(data)
    k_best = SelectKBest(f_classif, k=knum)
    k_best.fit(features, labels)

    feature_scorelist = zip(feature_set[1:], k_best.scores_)
    sort_feature_scorelist = sorted(feature_scorelist,key=lambda x: x[1],reverse=True)
    k_best_features = dict(sort_feature_scorelist[:knum])
    best_features = ['poi'] + k_best_features.keys()
    #print k_best_features
    return best_features


###function to calculate fraction
def computeFraction( poi_messages, all_messages ):
    fraction = 0.
    if all_messages == 'NaN':
        return fraction
    
    if poi_messages == 'NaN':
        poi_messages = 0
    
    fraction = 1.0*poi_messages/all_messages

    return fraction

###function to evaluate classifiers
def eval_clf(clf, features, labels, iters=1000, test_size=0.3):
    print clf
    accuracy = []
    precision = []
    recall = []
    first = True
    for iter in range(iters):
        features_train, features_test, labels_train, labels_test =cross_validation.train_test_split(features, labels, test_size=test_size)
        clf.fit(features_train, labels_train)
        pred = clf.predict(features_test)
        accuracy.append(accuracy_score(labels_test, pred))
        precision.append(precision_score(labels_test, pred))
        recall.append(recall_score(labels_test, pred))
        #f1.append(f1_score(labels_test, pred))
        if iter % 10 == 0:
            if first:
                sys.stdout.write('\nProcessing')
            sys.stdout.write('.')
            sys.stdout.flush()
            first = False

    print "done.\n"
    print "precision: {}".format(mean(precision))
    print "recall:    {}".format(mean(recall))
    print "accuracy:    {}".format(mean(accuracy))
    
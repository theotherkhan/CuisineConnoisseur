# driver.py
# Hasan Khan, Zach Danz
from setup import get_ingredients, get_recipes
import numpy as np
import sys
from tqdm import *
from NN import ANN
import pandas as pd

# Adjustable Hyperparameters
################################################
epochs = 2000
k = 6
l_rate = 0.01
################################################

global label_maps

if(len(sys.argv) < 3):
    sys.exit(-1)

ingr = get_ingredients(sys.argv[1])
recps = get_recipes(sys.argv[2], ingr[1])

label_maps = {"brazilian":0, "british":1, 
 "cajun_creole":2,"chinese":3,
 "filipino": 4,"french": 5,
 "greek": 6,"indian": 7,
 "irish": 8,"italian": 9,
 "jamaican": 10,
 "japanese": 11,
 "korean": 12,
 "mexican": 13,
 "moroccan": 14,
 "russian": 15,
 "southern_us": 16,
 "spanish": 17,
 "thai": 18,
 "vietnamese": 19}

#### PRE PROCESSING FUNCTIONS #######################################################

def label_vectors(training_labels, k_group_size, num_labels, def_label_init):
    ''' Generates numerical training label arrays, using recipe labels'''

    y = np.full([k_group_size, num_labels], def_label_init, dtype=float)
    
    for i in range (0, len(training_labels)):
        y[i][training_labels[i][0]] = 0.9
    
    return y

def cleanOutputDisplay(x):
    '''Cleans labels into a readable, interpretable format'''
    o = np.zeros_like(x)  
    for r in range (len(x)):
        o[r][np.argmax(x[r])] = 1
    
    o = np.asarray(o, dtype = int)
    return o

def cuisine_labels(testing_labels):
    '''Converts testing labels arrays into readable labels''' 
    cuisine_labels = np.empty([len(testing_labels)], dtype = str)

    for example in range(len(testing_labels)):
        output_label_id = np.argmax(testing_labels[example])

        for cuisine, idd in label_maps.items():  
            if idd == output_label_id:
                cuisine_labels[example] = cuisine

    return cuisine_labels

def acc(output, testing_labels):
    ''' Given output predictions and true labels, returns network accuracy'''
    match = 0.0
    for i in range (len(output)):
        if output[i] == testing_labels[i]:
            match+=1
    return float(match)/float(len(output))

def kfold(feature_clusters, label_clusters, k):
    ''' Returns a list of all possible train/test sets in accordance with given k-fold cross validation'''
    allPossible = []
    
    for i in range (k):
        
        testing_features = np.asarray(feature_clusters[i].tolist())
        testing_labels = np.asarray(label_clusters[i])
        #print "i: ", i
        if (i==0):
            training_features = np.concatenate(feature_clusters[i+1:].tolist())
            training_labels = np.concatenate(label_clusters[i+1:].tolist()) 
        elif(i==(k-1)):
            training_features = np.concatenate(feature_clusters[:i].tolist()) 
            training_labels = np.concatenate(label_clusters[:i].tolist())
        else: 
            training_features = np.concatenate( (np.concatenate(feature_clusters[i+1:].tolist()), np.concatenate(feature_clusters[:i].tolist())), axis=0)  
            training_labels = np.concatenate( (np.concatenate(label_clusters[i+1:].tolist()), np.concatenate(label_clusters[:i].tolist())), axis=0)  

        allPossible.append([training_features, training_labels, testing_features, testing_labels])
    
    return allPossible

def cf_validation(k, recps, num_datapoints):

    feature_clusters = np.empty([k, num_datapoints/k], dtype = list)
    label_clusters = np.empty([k, num_datapoints/k]) 

    for group in range(0, k):
        cluster_i = 0
        for i in range (0, len(recps)-1, k): 
            #while i < len(recps) 
            #print "group, cluster_i:", group, cluster_i
            feature_clusters[group][cluster_i] = (np.asarray(list(recps[i].ingredients), dtype = int)) 

            c_recipe = recps[i].uid.encode("ascii")
            label_clusters[group][cluster_i] = label_maps[c_recipe]

            cluster_i +=1

    return feature_clusters, label_clusters

#### RUN NN FUNCTION ##################################################################

def run(num_features, num_labels, num_hidden, training_features, training_labels, testing_features, testing_labels, loop_num):
    nn = ANN(num_features, num_labels, num_hidden)

    for e in tqdm(range(epochs), desc="K fold: "+str(loop_num), unit=" epochs"):

        output = nn.forward(training_features)
        #print "output shape:", output.shape
        #print ("\nOutput: ", output)

        cost = nn.cost(output, training_labels)
        avg_cost = sum(cost)/len(cost) 
        #print "\tAverage cost on epoch", e, ": ", avg_cost

        dJdW1, dJdW2, dJdB1, dJdB2 = nn.backprop(output, training_labels, training_features)

        '''
        print ("\nb1:", nn.b1)
        print ("\ndJdB1: ", dJdB1)      
        print ("\nb2:", nn.b2)
        print ("\ndJdB2: ", dJdB2)       
        print ("\nW1", nn.W1)
        print ("\ndJdW1: ", dJdW1)     
        print ("\nW2", nn.W2)
        print ("\ndJdW2: ", dJdW2)
        
        '''
        nn.w_update(dJdW1, dJdW2, dJdB1, dJdB2, l_rate)
        
        '''
        print ("\nUpdated B1: ", nn.b1)
        print ("\nUpdated B2: ", nn.b2)
        print ("\nUpdated Weight W1:", nn.W2)
        print ("\nUpdated Weight W2:", nn.W2)
        '''

    output = nn.forward(testing_features)

    cleanO = cleanOutputDisplay(output)
    cleanT = cleanOutputDisplay(testing_labels)

    #print "\nOutputs", output
    #print "\nClean outputs:\n ", pd.DataFrame(cleanO).head()
    #print "\nTesting labels:\n", pd.DataFrame(cleanT).head()

    #print "\n\tOutputs (r):\n ", cuisine_labels(output)
    #print "\n\tTesting labels (r): ", cuisine_labels(testing_labels)

    accuracy = acc( cuisine_labels(output), cuisine_labels(testing_labels)) 

    print "\tAccuracy: ", accuracy
    print "\tEnd cost: ", avg_cost
    return accuracy, avg_cost

#### DRIVER #######################################################################

# Define hyperparameters
num_features = len(ingr[1])
num_datapoints = 1794
num_labels = 20
num_hidden = 10 
k_group_size = num_datapoints / k
def_label_init = 0.005
accuracies = []
costs = []

# Build cross validation train/test
feature_clusters, label_clusters = cf_validation(k, recps, num_datapoints)

print "Program Started!"
# Run network
for i in range (k):
    
    training_features, training_labels, testing_features, testing_labels = kfold(feature_clusters, label_clusters, k)[i]
    
    testing_labels = np.reshape(testing_labels, (k_group_size, 1))
    testing_labels = label_vectors(testing_labels, k_group_size, num_labels, def_label_init)

    training_labels = np.reshape(training_labels, (k_group_size*(k-1), 1))
    training_labels = label_vectors(training_labels, k_group_size*(k-1), num_labels, def_label_init)

    '''
    print "TF types: ", type(training_features), type(training_features[0]), type(training_features[0][0])
    print "Training feature shapes: ", training_features.shape, training_features[0].shape, training_features[0][0].shape
    print "Testing feature shapes: ", testing_features.shape, testing_features[0].shape, testing_features[0][0].shape
    print "Training label shapes: ", training_labels.shape
    print "Testing label shapes: ", testing_labels.shape
    '''

    print "\n"
    accuracy, cost = run(num_features, num_labels, num_hidden, training_features, training_labels, testing_features, testing_labels, i)
    accuracies.append(accuracy)
    costs.append(cost)

# Calculate average accuracy and average cost
avg_accuracy = np.sum(accuracies)/len(accuracies) 
avg_cost = np.sum(costs)/len(costs)

print "\nAverage accuracies: ", avg_accuracy
print "Average costs: ", avg_cost

# End program

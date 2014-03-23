'''
Created on Jan 7, 2014

@author: bls910

This is a generalized version of the NaiveBayesClassifier from NLTK. I started with the version from nltk but this is very heavily changed now.
Some of the work done in the original NaiveBayesClassifier and my subclasses of it is now down in feature_types.py.

This is generalized in the sense that features can be of different sorts. In the original,  each feature could have one of three values - true, false, and none.
This generalized version can have features of any of the types in feature types.
s
'''

from nltk.probability import FreqDist, ELEProbDist, DictionaryProbDist # @UnresolvedImport

class GeneralizedNaiveBayesClassifier(object):
    
    def __init__(self, label_probdist, feature_dict, params):
        self._label_probdist = label_probdist
        self._feature_dict = feature_dict
        self._labels = label_probdist.samples()
   
    @staticmethod
    def train(labeled_featuresets, feature_dict, params = None, estimator=ELEProbDist):
        
        # Do the work to train each of the feature given each featureset.
        # Also count up the occurrences of each label
        # feature_dict is a dictionary of feature_types indexed by featurename
        
        label_freqdist = FreqDist()
        for featureset, label in labeled_featuresets:
            label_freqdist.inc(label)
            for fname in featureset.keys():
                feature_dict[fname].train_on_instance(label, featureset[fname])

        # Create the P(label) distribution
        label_probdist = estimator(label_freqdist)

        # Create the P(fval|label, fname) distributions. This is done in the feature type classes
        for [fname, f] in feature_dict.items():
            f.compute_distributions()

        return GeneralizedNaiveBayesClassifier(label_probdist, feature_dict, params)

    def prob_classify(self, featureset):
        
        # Discard any feature names that we've never seen before.
        # Otherwise, we'll just assign a probability of 0 to
        # everything.
        featureset = featureset.copy()
        for fname in featureset.keys():
            if fname in self._feature_dict:
                    break
            else:
                #print 'Ignoring unseen feature %s' % fname
                del featureset[fname]

        # Find the log probabilty of each label, given the features.
        # Start with the log probability of the label itself.
        logprob = {}
        for label in self._labels:
            logprob[label] = self._label_probdist.logprob(label)

        # Then add in the log probability of features given labels.
        for label in self._labels:
            for fname in featureset.keys():
                fval = featureset[fname]
                logprob[label] +=  self._feature_dict[fname].weighted_logprob(label, fval)

        return DictionaryProbDist(logprob, normalize=True, log=True)

    def classify(self, featureset):
        return self.prob_classify(featureset).max()
    
    # The classes below are used to extract some information I use for displays of various internals.
    
    def get_raw_counts(self):
        data_dict = {}
        for (fname, fe) in self._feature_dict.items():
            data_dict[fname] = {}
            data_dict[fname]["feature"] = {}
            data_dict[fname]["feature"][" "] = fname
            for label in fe.labels:
                data_dict[fname][label] = {}
                for fval in fe.fvals:
                    data_dict[fname][label][fval] = fe.data[label][fval]
        return data_dict
    
    def get_logprobs_for_featureval(self, fname, fval):
        result_dict = {}
        for label in self._labels:
            result_dict[label] =  self._feature_dict[fname].weighted_logprob(label, fval)
        return result_dict
     
    def get_label_base_logprobs(self):
        logprob = {}
        for label in self._labels:
            logprob[label] = self._label_probdist.logprob(label)
        return logprob
     
    def get_final_logprobs_for_featureset(self, featureset):
        full_result = self.prob_classify(featureset)
        return full_result._prob_dict
             

    
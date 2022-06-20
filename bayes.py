import numpy as np

# TODO: Maybe replace with sets

# A class that utilizes bayes theorem to classify messages.
class NaiveBayes():
    
    # Initializes a NaiveBayes class used to classify given messages into
    # based or cringe
    def __init__(self):
        self.num_cringe = 0
        self.num_based = 0
        self.cringe_wc = {}
        self.based_wc = {}

    # Trains the data given a path to a cringe file and a based file
    # Files must be formatted with one message per line
    def train(self, cringe, based):
        with open(cringe, 'r') as cringe_file:
            for line in cringe_file:
                self.num_cringe += 1
                self.process_line(line, self.cringe_wc)
        
        with open(based, 'r') as based_file:
            for line in based_file:
                self.num_based += 1
                self.process_line(line, self.based_wc)

    # Helper function to reduce some redundancy. Iterates through words
    # in a line, updating given word count map appropriately
    def process_line(self, line, wc):
        for word in line.split():
            wc[word] = wc.get(word, 0) + 1


    # Returns true if the given message is 'cringe' and false if 'based'
    # Assumes the message has already been properly formated such that 
    # it matched the training data
    def predict(self, message):
        cringe = 0
        based = 0
        
        message_wc = {}
        self.process_line(message, message_wc)

        for word, count in message_wc:
            cringe += np.log(count * (self.cringe_wc.get(word, 0) + 1) / 
                                     (self.num_cringe + 2))
            based += np.log(based * (self.based_wc.get(word, 0) + 1) / 
                                    (self.num_based + 2))

        return cringe > based
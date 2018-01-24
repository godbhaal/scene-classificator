import os
import time

import numpy as np
from keras import Model, Input, optimizers
from keras.layers import Dense, Flatten, Dropout, Conv2D, MaxPooling2D
from keras.utils import plot_model
from matplotlib import pyplot as plt

from data_generator import DataGenerator
from data_generator_config import DataGeneratorConfig
from evaluator import Evaluator


class CNN(object):
    def __init__(self,
                 logger,
                 dataset_dir='/home/datasets/scenes/MIT_split',
                 model_fname='my_first_mlp.h5'):

        # Default parameters (used if no `set_*` is called)
        self.model = self._default_model()
        self.optimizer = optimizers.Adadelta(lr=0.1)
        self.batch_size = 32

        self.history = None
        self.dataset_dir = dataset_dir
        self.model_fname = model_fname
        self.logger = logger
        self.logger.info('Creating object')

    def set_optimizer(self, optimizer):  # type: (optimizers.Optimizer) -> None
        self.optimizer = optimizer

    def set_model(self, model):  # type: (Model) -> None
        self.model = model

    def set_batch_size(self, batch_size):
        self.batch_size = batch_size

    def configure(self):
        """ Reconfigures the neural network in case any parameter changed.

        It must be used after calling the methods named as `set_*`. It can be
        used after all the setters are run (not need to configure for each one)
        See `set_optimizer`, `set_model`, `set_batch_size`
        """
        image_width, image_height = \
            self.model.input_shape[1], self.model.input_shape[2]
        # create data generator objects
        self.data_gen_test = \
            DataGenerator(image_width, image_height, self.batch_size,
                          '{}/train'.format(self.dataset_dir))
        self.data_gen_test.configure(DataGeneratorConfig.NORMALISE)

        self.test_generator = self.data_gen_test.get_single(
            path='{}/testCNN'.format(self.dataset_dir), shuffle=False)

        self.validation_generator = self.data_gen_test.get_single(
            path='{}/validationCNN'.format(self.dataset_dir))

        self.data_gen_train = \
            DataGenerator(image_width, image_height, self.batch_size,
                          '{}/train'.format(self.dataset_dir))

        self.data_gen_train.configure(DataGeneratorConfig.NORM_AND_TRANSFORM)

        self.train_generator = self.data_gen_train.get_single(
            path='{}/train'.format(self.dataset_dir))

        if not os.path.exists(self.dataset_dir):
            self.logger.info('ERROR: dataset directory {} do not exists!'.
                             format(self.dataset_dir))

    def _default_model(self):
        main_input = Input(
            shape=(256, 256, 3), dtype='float32', name='main_input')

        x = Conv2D(32, (3, 3), activation='relu', name='conv1')(main_input)
        x = Conv2D(32, (3, 3), activation='relu', name='conv2')(x)
        x = MaxPooling2D(pool_size=(4, 4), padding='valid', name='pool')(x)
        x = Flatten()(x)
        x = Dense(256, activation='relu', name='fc1')(x)
        x = Dense(128, activation='relu', name='fc2')(x)
        x = Dropout(0.5)(x)

        main_output = Dense(
            units=8, activation='softmax', name='predictions')(x)

        return Model(inputs=main_input, outputs=main_output)

    def build(self):
        """ Run after configuing the neural network.

        See `configure()`
        """
        init = time.time()
        self.logger.info('Compiling MLP model...')

        # Compile the model
        self.model.compile(loss='categorical_crossentropy',
                           optimizer=self.optimizer,
                           metrics=['accuracy'])

        print(self.model.summary())
        self.logger.info('Summary: {}'.format(self.model.summary()))

        plot_model(
            self.model,
            to_file='../results/session5/CNN_{}.png'.format(self.model.name),
            show_shapes=True,
            show_layer_names=True)

        end = time.time()
        self.logger.info('Done in {} secs.'.format(str(end - init)))

    def train_CNN_model(self, n_epochs, steps_per_epoch, validation_steps):
        # train the CNN model
        init = time.time()

        if os.path.exists(self.model_fname):
            self.logger.info('WARNING: model file {} exists and will be '
                             'overwritten!'.format(self.model_fname))

        self.logger.info('Start training...')

        # The dataset train contains 1881 images (70%)
        # The dataset validationCNN contains 320 images (12%)
        # The dataset testCNN contains 487 images (18%)

        self.history = self.model.fit_generator(
            generator=self.train_generator,
            # steps_per_epoch=10 * 1881 // self.batch_size,
            steps_per_epoch=1,
            epochs=n_epochs,
            validation_data=self.validation_generator,
            # validation_steps=807 // self.batch_size)
            validation_steps=1)

        self.logger.info('Done!')
        self.logger.info('Saving the model into {}'.format(self.model_fname))
        # always save your weights after training or during training
        self.model.save_weights(self.model_fname)
        self.logger.info('Done!')

        end = time.time()
        self.logger.info('Done in {} secs.'.format(str(end - init)))

    def load_CNN_model(self):
        init = time.time()

        if not os.path.exists(self.model_fname):
            self.logger.info(
                'Error: model file {} exists and will be overwritten!'.format(
                    self.model_fname))

        self.logger.info('Loading the model from {}'.format(self.model_fname))
        # always save your weights after training or during training
        self.model.load_weights(self.model_fname)
        self.logger.info('Done!')

        end = time.time()
        self.logger.info('Done in {} secs.'.format(str(end - init)))

    def plot_history(self):
        # summarize history for accuracy
        plt.plot(self.history.history['acc'])
        plt.plot(self.history.history['val_acc'])
        plt.title('model accuracy')
        plt.ylabel('accuracy')
        plt.xlabel('epoch')
        plt.legend(['train', 'validation'], loc='upper left')
        plt.savefig('results/session5/accuracy.jpg')
        plt.close()

        # summarize history for loss
        plt.plot(self.history.history['loss'])
        plt.plot(self.history.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['train', 'validation'], loc='upper left')
        plt.savefig('results/session5/loss.jpg')

    def plot_results(self):
        # plot classification results
        self.logger.info('Getting classification results...')
        init = time.time()

        scores, evaluator = self.get_results()

        self.logger.info(
            'Evaluator \n'
            'Acc (model) {}\n'
            'Accuracy: {} \n'
            'Precision: {} \n'
            'Recall: {} \n'
            'Fscore: {}'.format(scores[1], evaluator.accuracy,
                                evaluator.precision, evaluator.recall,
                                evaluator.fscore))

        # Plot the confusion matrix on test data
        cm = evaluator.confusion_matrix()
        self.logger.info('Confusion matrix:')
        self.logger.info(cm)

        plt.matshow(cm)
        plt.title('Confusion matrix')
        plt.colorbar()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')
        plt.show()
        plt.savefig('results/session5/cm.jpg')
        self.logger.info(
            'Final accuracy: {}'.format(str(evaluator.accuracy)))

        end = time.time()
        self.logger.info('Done in {} secs.'.format(str(end - init)))

    def get_results(self):
        test_labels = self.test_generator.classes

        # Predict test images
        predictions_raw = self.model.predict_generator(self.test_generator)
        predictions = []
        for prediction in predictions_raw:
            predictions.append(np.argmax(prediction))
        # Evaluate results
        evaluator = Evaluator(test_labels, predictions,
                              label_list=list([0, 1, 2, 3, 4, 5, 6, 7]))

        #
        scores = self.model.evaluate_generator(self.test_generator)
        self.logger.info(
            'Evaluator \n'
            'Acc (model) {}\n'
            'Accuracy: {} \n'
            'Precision: {} \n'
            'Recall: {} \n'
            'Fscore: {}'.format(scores[1], evaluator.accuracy,
                                evaluator.precision, evaluator.recall,
                                evaluator.fscore))

        return scores, evaluator

    def cross_validate(self):
        init = time.time()
        # TODO cross validate the MLP model

        end = time.time()
        self.logger.info('Done in {} secs.'.format(str(end - init)))
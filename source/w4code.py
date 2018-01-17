from keras import backend as K
from keras.applications.vgg16 import VGG16
from keras.layers import Dense
from keras.models import Model
from keras.preprocessing.image import ImageDataGenerator
from keras.utils.vis_utils import plot_model as plot
import matplotlib.pyplot as plt

from source import TEST_PATH
from source import TRAIN_PATH

VALIDATION_PATH = TEST_PATH
img_width = 224
img_height = 224
batch_size = 32
number_of_epoch = 20


def preprocess_input(x, dim_ordering='default'):
    if dim_ordering == 'default':
        dim_ordering = K.image_dim_ordering()
    assert dim_ordering in {'tf', 'th'}

    if dim_ordering == 'th':
        # 'RGB'->'BGR'
        x = x[::-1, :, :]
        # Zero-center by mean pixel
        x[0, :, :] -= 103.939
        x[1, :, :] -= 116.779
        x[2, :, :] -= 123.68
    else:
        # 'RGB'->'BGR'
        x = x[:, :, ::-1]
        # Zero-center by mean pixel
        x[:, :, 0] -= 103.939
        x[:, :, 1] -= 116.779
        x[:, :, 2] -= 123.68
    return x


# create the base pre-trained model
base_model = VGG16(weights='imagenet')
plot(base_model, to_file='modelVGG16a.png', show_shapes=True,
     show_layer_names=True)

x = base_model.layers[-2].output
x = Dense(8, activation='softmax', name='predictions')(x)

model = Model(input=base_model.input, output=x)
plot(model, to_file='modelVGG16b.png', show_shapes=True, show_layer_names=True)
for layer in base_model.layers:
    layer.trainable = False

model.compile(loss='categorical_crossentropy', optimizer='adadelta',
              metrics=['accuracy'])
for layer in model.layers:
    print(layer.name, layer.trainable)

# preprocessing_function=preprocess_input,
datagen = ImageDataGenerator(featurewise_center=False,
                             samplewise_center=False,
                             featurewise_std_normalization=False,
                             samplewise_std_normalization=False,
                             preprocessing_function=preprocess_input,
                             rotation_range=0.,
                             width_shift_range=0.,
                             height_shift_range=0.,
                             shear_range=0.,
                             zoom_range=0.,
                             channel_shift_range=0.,
                             fill_mode='nearest',
                             cval=0.,
                             horizontal_flip=False,
                             vertical_flip=False,
                             rescale=None)

train_generator = datagen.flow_from_directory(TRAIN_PATH,
                                              target_size=(
                                                  img_width, img_height),
                                              batch_size=batch_size,
                                              class_mode='categorical')

test_generator = datagen.flow_from_directory(TEST_PATH,
                                             target_size=(
                                                 img_width, img_height),
                                             batch_size=batch_size,
                                             class_mode='categorical')

validation_generator = datagen.flow_from_directory(VALIDATION_PATH,
                                                   target_size=(
                                                       img_width, img_height),
                                                   batch_size=batch_size,
                                                   class_mode='categorical')
history = model.fit_generator(train_generator,
                              steps_per_epoch=(int(
                                  400 * 1881 / 1881 // batch_size) + 1),
                              epochs=number_of_epoch,
                              validation_data=validation_generator,
                              validation_steps=807)

result = model.evaluate_generator(test_generator, val_samples=807)
print(result)

# list all data in history

if False:
    # summarize history for accuracy
    plt.plot(history.history['acc'])
    plt.plot(history.history['val_acc'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'validation'], loc='upper left')
    plt.savefig('accuracy.jpg')
    plt.close()
    # summarize history for loss
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'validation'], loc='upper left')
    plt.savefig('loss.jpg')
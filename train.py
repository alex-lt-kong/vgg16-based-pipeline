from tensorflow import keras

import utils
import logging
import matplotlib.pyplot as plt
import os
import pandas as pd
import json
import shutil
import sys
import tensorflow as tf

settings = {}

def preview_samples(dest_dir: str, dataset: tf.data.Dataset, data_augmentation):

    count = {
        '0': 0,
        '1': 0
    }
    dataset = dataset.shuffle(buffer_size=128)
    for images, labels in dataset:
        augmented_images = data_augmentation(images)
        for i in range(len(augmented_images)):
            label = str(labels[i].numpy())
            count[label] += 1
            label_dir = os.path.join(dest_dir, label)
            if os.path.isdir(label_dir) is False:
                os.mkdir(label_dir)

            tf.keras.utils.save_img(
                os.path.join(label_dir, f'{count[label]}.jpg'), augmented_images[i].numpy().astype("uint8")
            )

        enough_sample = 0
        for key in count.keys():
            if count[key] > 5:
                enough_sample += 1
        if enough_sample >= len(count.keys()):
            break

def save_model(model) -> None:
    if os.path.isdir(settings['model']['save_to']['model']):
        shutil.rmtree(settings['model']['save_to']['model'])
    
    tf.keras.models.save_model(
        model=model, filepath=settings['model']['save_to']['model']
    )

def save_stats_and_plots(history: keras.callbacks.History) -> None:
    df = pd.DataFrame(data=history.history)
    df['auc_ma'] = df['auc'].rolling(window=5).mean()
    df['val_auc_ma'] = df['val_auc'].rolling(window=5).mean()
    df.to_csv(settings['model']['save_to']['history'])
    plt.figure(figsize = (16/2, 9/2))
    plt.rcParams.update({'font.size': 15})
    #fig = df[['AUC', 'AUC_ma', 'val_AUC', 'val_AUC_ma']].plot(kind='line', figsize=(16, 9/2), fontsize=12).get_figure()
    plt.plot(df['auc'],     linewidth=1.75, label="auc",     color='C0')    
    plt.plot(df['val_auc'], linewidth=1.75, label="val_auc", color='C1')
    plt.legend()
    plt.xlabel('Epochs')
    plt.ylabel('AUC')
    plt.savefig(
        settings['model']['save_to']['historical_auc_plot'], bbox_inches='tight'
    )

    # clear figure
    plt.clf()

    plt.figure(figsize = (16/2, 9/2))
    plt.rcParams.update({'font.size': 15})
    # df['loss'].iloc[0] could be huge, let's exclude it..
    plt.plot(df['loss'].iloc[1:],     linewidth=1.75, label="loss",     color='C0')    
    plt.plot(df['val_loss'].iloc[1:], linewidth=1.75, label="val_loss", color='C1')
    plt.yscale('log')
    plt.legend()
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.savefig(
        settings['model']['save_to']['historical_loss_plot'], bbox_inches='tight'
    )

    

def main():
    utils.set_environment_vars()
    global settings
    settings = utils.read_config_file()
    utils.initialize_logger()
    sys.path.insert(1, settings['model']['path'])
    import definition
    
    image_size = definition.target_image_size


    
    logging.info(settings)
    logging.info('Checking valid GPUs')
    utils.check_gpu()
    #logging.info('Removing invalid samples, this could take a while...')
    #utils.remove_invalid_samples(settings['dataset']['path'])
    logging.info('Separating data into a training set and a test set')
    train_ds, val_ds = utils.prepare_dataset(
        settings['dataset']['path'],
        image_size=image_size,
        batch_size=definition.batch_size
    )

    func = definition.data_augmentation()
    logging.info('Saving some samples as preview')
    preview_samples(
        dest_dir=settings['dataset']['preview_save_to'],
        dataset=train_ds,
        data_augmentation=func)
    
    logging.info('calling make_model()')
    model = definition.make_model(
        input_shape=image_size + (3,), data_augmentation=func, num_classes=2
    )

    # https://stackoverflow.com/questions/55908188/this-model-has-not-yet-been-built-error-on-model-summary
    keras.utils.plot_model(
        model, show_shapes=True,
        to_file=settings['model']['save_to']['model_plot']
    )

    with open(settings['model']['save_to']['summary'], 'w') as f:        
        model.summary(print_fn=lambda x: f.write(x + '\n'))
    with open(settings['model']['save_to']['optimizer_config'], "w") as f:
        f.write(str(model.optimizer.get_config()))

    history = model.fit(
        train_ds, epochs=definition.epochs, validation_data=val_ds
    )
    assert isinstance(history, keras.callbacks.History)
    
    save_model(model)
    save_stats_and_plots(history)
    

if __name__ == '__main__':
    main()

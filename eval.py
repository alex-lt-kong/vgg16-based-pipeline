from typing import List, Tuple
from sklearn import metrics
from sklearn.metrics import classification_report
from tensorflow import keras

import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import seaborn as sn
import shutil
import sys
import tensorflow as tf
import utils


def get_predictions(dataset: tf.data.Dataset, model: keras.models.Model,
    misclassified_dest: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # X = np.concatenate([X for X, y in val_ds], axis=0)    
    # y_true = np.concatenate([y for x, y in val_ds], axis=0)
    # cannot use this approach as it loads all the samples into memory, which 
    # gets exhausted very fast.
    if os.path.isdir(misclassified_dest) is True:
        shutil.rmtree(misclassified_dest)
    os.mkdir(misclassified_dest)
    y_true = np.empty((0,))
    y_pred = np.empty((0,))
    y_pred_cat = np.empty((0,))
    counts = [0, 0]

    for x, y_true_batch in dataset:
        # Note that here x and y do not come one after another--they come in batches
        # whose size is defined by the batch_size parameter passed to the prepare_dataset
        # method.

        y_true_batch = y_true_batch.numpy()
        y_true = np.concatenate((y_true, y_true_batch))
        y_pred_batch = model.predict(x).flatten()
        assert isinstance(y_pred_batch, np.ndarray)
        y_pred_cat_batch = np.where(y_pred_batch < 0.5, 0, 1)
        y_pred = np.concatenate((y_pred, y_pred_batch))
        y_pred_cat = np.concatenate((y_pred_cat, y_pred_cat_batch))
        for i in range(len(y_pred_cat_batch)):

            assert y_true_batch[i] in [0, 1]
            if y_pred_cat_batch[i] == y_true_batch[i]:
                continue
            counts[y_true_batch[i]] += 1
            label_dir = os.path.join(
                misclassified_dest, f'true_label_{y_true_batch[i]}'
            )
            if os.path.isdir(label_dir) is False:
                os.mkdir(label_dir)
            tf.keras.utils.save_img(
                os.path.join(
                    label_dir, f'{counts[y_true_batch[i]]:03d}.jpg'
                ),
                x[i].numpy().astype("uint8")
            )
        #breakpoint()

    return y_true, y_pred, y_pred_cat


def plot_confusion_matrix(
    y_true: np.ndarray, y_pred_cat: np.ndarray, classes: List[str], path: str
) -> None:
    cm = metrics.confusion_matrix(y_true, y_pred_cat)
    
    df_cm = pd.DataFrame(cm, index=classes, columns=classes)
    plt.clf()
    plt.figure(figsize = (16/2, 9/2))
    plt.rcParams.update({'font.size': 15})
    sn.heatmap(df_cm, cmap="YlGnBu", annot=True, fmt='g')    
    plt.xlabel('Predicted label')
    plt.ylabel('True label')
    plt.savefig(path, bbox_inches='tight')

    print(cm)


def plot_roc_curve(y_true_train: np.ndarray, y_true_val: np.ndarray,
    y_pred_train: np.ndarray, y_pred_val: np.ndarray, path: str) -> None:
    
    plt.clf()
    plt.figure(figsize = (16/2, 9/2))
    plt.rcParams.update({'font.size': 15})
    fpr_train, tpr_train, thresholds_train = metrics.roc_curve(
        y_true_train, y_pred_train
    )
    fpr_val, tpr_val, thresholds_val = metrics.roc_curve(
        y_true_val, y_pred_val
    )

    # plot both ROC curves on the same graph
    plt.plot(fpr_train, tpr_train, label='Train')
    plt.plot(fpr_val, tpr_val, label='Val')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.legend()
    plt.savefig(path, bbox_inches='tight')


def main() -> None:

    settings = utils.read_config_file()
    utils.initialize_logger()
    sys.path.insert(1, settings['model']['path'])
    import definition    
    image_size = definition.target_image_size     
    

    train_ds, val_ds = utils.prepare_dataset(
        settings['dataset']['path'],
        image_size=image_size,
        batch_size=definition.batch_size,
        seed=settings['dataset']['validation_split_seed']
    )
    model = tf.keras.models.load_model(settings['model']['save_to']['model'])

    classes = ['Not Detected', 'Detected']

    y_true_train, y_pred_train, y_pred_cat_train = get_predictions(
        dataset=train_ds, model=model,
        misclassified_dest=settings['diagnostics']['misclassified_train']
    )
    plot_confusion_matrix(y_true_train, y_pred_cat_train,
        classes, settings['diagnostics']['confusion_matrix_train'])
    
    y_true_val, y_pred_val, y_pred_cat_val = get_predictions(
        dataset=val_ds, model=model,
        misclassified_dest=settings['diagnostics']['misclassified_val']
    )
    plot_confusion_matrix(y_true_val, y_pred_cat_val, classes,
        settings['diagnostics']['confusion_matrix_val'])
    with open(settings['diagnostics']['report'], 'w') as f:
        f.write(classification_report(y_true_val, y_pred_cat_val,
            target_names=classes))

    plot_roc_curve(y_true_train, y_true_val, y_pred_train, y_pred_val,
        settings['diagnostics']['roc'])

if __name__ == '__main__':
    main()
